"""US-3: storing uitlezen uit foto en tekst met Claude.

Claude geeft een vast JSON-schema terug. Daarna controleert `controleer()` de
uitvoer voordat de werkstroom verdergaat: wat niet te lezen is blijft leeg, en
spoed is altijd een voorstel met een reden.
"""

import base64
import re

import anthropic
from pydantic import BaseModel, Field

from app import config

BEKENDE_MERKEN = ["Remeha", "Intergas", "Nefit", "Vaillant", "Bosch", "ATAG", "Itho Daalderop", "Viessmann", "AWB"]

# Woorden die op een gok wijzen; zulke waarden maken we leeg.
# Vergeleken zonder punten en spaties, dus "n.v.t." en "niet leesbaar" vallen er ook onder.
GOKWOORDEN = {"onbekend", "unknown", "nvt", "n/a", "?", "-", "nietleesbaar", "nietzichtbaar", "geen"}

SYSTEEMPROMPT = f"""Je leest storingsmeldingen uit voor een installatiebedrijf in Nederland.
Een klant stuurt tekst en soms een foto van zijn cv-ketel, het display of het typeplaatje.

Vul alleen in wat je echt kunt lezen of wat de klant letterlijk schrijft. Gok nooit.
Kun je een veld niet met zekerheid lezen, laat het dan leeg (null). Een leeg veld is beter dan een fout veld.

- merk: fabrikant van het toestel, zoals {", ".join(BEKENDE_MERKEN)}.
- type: typeaanduiding van het toestel zoals op het typeplaatje of in de tekst (bijv. "Calenta Ace 28C", "HRE 28/24").
- foutcode: de code op het display of uit de tekst, precies zoals geschreven (bijv. "F28", "EA", "F.22", "H02.02").
- klacht: in één korte, zakelijke zin wat er mis is, in het Nederlands.
- spoed: jouw voorstel, true of false. Spoed is bijvoorbeeld: geen verwarming, geen warm water,
  waterlekkage, kwetsbare bewoners genoemd. Geen spoed: geluid, kleine druppel, onderhoudsvraag.
- spoed_reden: altijd invullen, één korte zin waarom wel of geen spoed.
"""


class Uitlezing(BaseModel):
    """Vast schema voor de uitvoer van Claude."""

    merk: str | None = Field(description="Merk van het toestel, of null als niet te lezen")
    type: str | None = Field(description="Typeaanduiding, of null als niet te lezen")
    foutcode: str | None = Field(description="Foutcode precies zoals getoond, of null")
    klacht: str | None = Field(description="Korte omschrijving van de klacht, of null")
    spoed: bool = Field(description="Voorstel: is dit spoed?")
    spoed_reden: str = Field(description="Korte reden voor het spoedvoorstel")


class UitleesFout(Exception):
    pass


def _leeg_als_gok(waarde: str | None, max_lengte: int) -> str | None:
    if waarde is None:
        return None
    waarde = " ".join(waarde.split())
    if not waarde or re.sub(r"[\s.]", "", waarde.lower()) in GOKWOORDEN or len(waarde) > max_lengte:
        return None
    return waarde


def controleer(u: Uitlezing) -> dict:
    """Controle vóór de werkstroom verdergaat. Geeft een schone dict terug."""
    merk = _leeg_als_gok(u.merk, 40)
    if merk:
        # Schrijfwijze gelijktrekken met de bekende lijst ("remeha" -> "Remeha").
        merk = next((m for m in BEKENDE_MERKEN if m.lower() == merk.lower()), merk)

    foutcode = _leeg_als_gok(u.foutcode, 12)
    if foutcode and not re.fullmatch(r"[A-Za-z0-9.\-/ ]+", foutcode):
        foutcode = None
    if foutcode:
        foutcode = foutcode.upper()

    reden = _leeg_als_gok(u.spoed_reden, 200)
    if not reden:
        raise UitleesFout("Spoedvoorstel zonder reden; uitvoer afgekeurd.")

    return {
        "merk": merk,
        "type": _leeg_als_gok(u.type, 60),
        "foutcode": foutcode,
        "klacht": _leeg_als_gok(u.klacht, 300),
        "spoed": u.spoed,
        "spoed_reden": reden,
    }


def lees_uit(tekst: str, foto: bytes | None = None, media_type: str = "image/jpeg") -> dict:
    """Stuurt tekst (en foto) naar Claude en geeft de gecontroleerde uitlezing terug."""
    if not config.ANTHROPIC_API_KEY:
        raise UitleesFout("ANTHROPIC_API_KEY ontbreekt in .env")

    inhoud: list[dict] = []
    if foto:
        inhoud.append({
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": base64.standard_b64encode(foto).decode()},
        })
    inhoud.append({"type": "text", "text": f"Bericht van de klant:\n{tekst or '(geen tekst, alleen een foto)'}"})

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY, timeout=60.0)
    try:
        antwoord = client.beta.messages.parse(
            model=config.CLAUDE_MODEL,
            max_tokens=4000,
            system=SYSTEEMPROMPT,
            messages=[{"role": "user", "content": inhoud}],
            output_format=Uitlezing,
            thinking={"type": "adaptive"},
            output_config={"effort": config.CLAUDE_EFFORT},
            # Bij een onterechte weigering neemt de API automatisch een ander model.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
    except anthropic.APIConnectionError as fout:
        raise UitleesFout("AI-dienst niet bereikbaar") from fout
    except anthropic.RateLimitError as fout:
        raise UitleesFout("AI-dienst is even overbelast") from fout
    except anthropic.APIStatusError as fout:
        raise UitleesFout(f"AI-dienst gaf fout {fout.status_code}: {fout.message}") from fout

    if antwoord.stop_reason == "refusal":
        raise UitleesFout("AI weigerde het verzoek")
    if antwoord.stop_reason == "max_tokens" or antwoord.parsed_output is None:
        raise UitleesFout("AI-uitvoer onvolledig")
    return controleer(antwoord.parsed_output)
