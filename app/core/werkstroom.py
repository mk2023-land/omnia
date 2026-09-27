"""De werkstroom: wat OMNIA doet met een binnenkomend bericht van een klant.

Volgorde:
  1. Gaslucht-controle (US-2): vaste regel, altijd eerst, geen AI.
  2. AI-stap (US-3): storing uitlezen uit tekst en foto.
"""

from collections.abc import Callable

from app import config
from app.core import berichten
from app.core.logboek import Logboek
from app.core.veiligheid import NOODNUMMER_GAS, controleer_gaslucht, veiligheidsbericht

# Een AI-stap krijgt tekst, foto (of None) en het beeldtype, en geeft een uitlezing terug.
AiStap = Callable[[str, bytes | None, str], dict]


def verwerk_bericht(
    logboek: Logboek,
    klant: str,
    tekst: str,
    foto: bytes | None = None,
    media_type: str = "image/jpeg",
    foto_url: str | None = None,
    ai_stap: AiStap | None = None,
) -> dict:
    logboek.schrijf(klant, "bericht_in", tekst=tekst, foto_url=foto_url)

    # 1. Gaslucht gaat altijd voor, vóór elke AI-stap.
    treffer = controleer_gaslucht(tekst)
    if treffer:
        berichten.verstuur(logboek, klant, veiligheidsbericht(config.BEDRIJFSNAAM))
        logboek.schrijf(
            klant,
            "gasmelding",
            tekst=tekst,
            reden=treffer.reden,
            woorden=list(treffer.woorden),
            noodnummer=NOODNUMMER_GAS,
        )
        return {"route": "gasmelding", "reden": treffer.reden}

    # 2. Gewone rij. De AI-stap draait direct als die is meegegeven,
    #    anders plant de aanroeper hem zelf in (op de achtergrond).
    logboek.schrijf(klant, "gewone_rij", tekst=tekst)
    if ai_stap is None:
        return {"route": "gewone_rij"}
    return {"route": "gewone_rij", **ai_uitlezen(logboek, klant, tekst, foto, media_type, ai_stap)}


def ai_uitlezen(
    logboek: Logboek, klant: str, tekst: str, foto: bytes | None, media_type: str, ai_stap: AiStap
) -> dict:
    """Leest de storing uit. Mag falen zonder dat er iets misgaat: de melding staat al in de rij."""
    try:
        uitlezing = ai_stap(tekst, foto, media_type)
    except Exception as fout:  # noqa: BLE001 - AI-dienst onbereikbaar of uitvoer afgekeurd
        logboek.schrijf(klant, "ai_fout", fout=str(fout))
        return {"ai_fout": str(fout)}
    logboek.schrijf(klant, "ai_uitvoer", **uitlezing)
    berichten.verstuur(logboek, klant, bevestiging(uitlezing))
    return {"ai": uitlezing}


def bevestiging(u: dict) -> str:
    """Bericht aan de klant: wat we genoteerd hebben, en wat er eventueel nog ontbreekt."""
    regels = [
        f"Bedankt! Dit hebben we genoteerd voor {config.BEDRIJFSNAAM}:",
        f"• Merk: {u.get('merk') or '–'}",
        f"• Type: {u.get('type') or '–'}",
        f"• Foutcode: {u.get('foutcode') or '–'}",
    ]
    if u.get("klacht"):
        regels.append(f"• Klacht: {u['klacht']}")
    ontbreekt = [naam for naam in ("merk", "type") if not u.get(naam)]
    if ontbreekt:
        regels.append(f"\nKunt u nog een foto van het typeplaatje sturen? Dan weten we ook het {' en '.join(ontbreekt)}.")
    regels.append("\nWe sturen u zo snel mogelijk een tijd voor de monteur.")
    return "\n".join(regels)
