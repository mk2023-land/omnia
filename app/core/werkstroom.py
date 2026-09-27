"""De werkstroom: wat OMNIA doet met een binnenkomend bericht van een klant.

Volgorde:
  1. Gaslucht-controle (US-2): vaste regel, altijd eerst, geen AI.
  2. AI-stap (US-3): storing uitlezen. Volgt nog.
"""

from collections.abc import Callable

from app import config
from app.core import berichten
from app.core.logboek import Logboek
from app.core.veiligheid import NOODNUMMER_GAS, controleer_gaslucht, veiligheidsbericht

# Een AI-stap krijgt de tekst van de klant en geeft een resultaat terug.
AiStap = Callable[[str], dict]


def verwerk_bericht(logboek: Logboek, klant: str, tekst: str, ai_stap: AiStap | None = None) -> dict:
    logboek.schrijf(klant, "bericht_in", tekst=tekst)

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

    # 2. Gewone rij. De AI-stap mag falen zonder dat er iets misgaat.
    if ai_stap is None:
        logboek.schrijf(klant, "gewone_rij", tekst=tekst)
        return {"route": "gewone_rij"}
    try:
        resultaat = ai_stap(tekst)
    except Exception as fout:  # noqa: BLE001 - AI-dienst onbereikbaar of foutief
        logboek.schrijf(klant, "ai_fout", fout=str(fout))
        return {"route": "gewone_rij", "ai_fout": str(fout)}
    logboek.schrijf(klant, "ai_uitvoer", **resultaat)
    return {"route": "gewone_rij", "ai": resultaat}
