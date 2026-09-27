"""Instellingen voor de OMNIA-demo.

Alles staat hier op één plek en komt uit het .env-bestand (zie .env.example).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _bool(naam: str, standaard: bool) -> bool:
    waarde = os.getenv(naam)
    if waarde is None:
        return standaard
    return waarde.strip().lower() in {"1", "true", "ja", "yes", "aan"}


# Fictieve bedrijfsnaam die in alle berichten aan de klant staat.
BEDRIJFSNAAM = os.getenv("BEDRIJFSNAAM", "Installatiebedrijf De Vries")

# Simulatie: externe diensten (Twilio, WhatsApp, Google) worden nagebootst.
# Zet per dienst op false zodra het echte account klaarstaat.
SIMULATIE_TELEFONIE = _bool("SIMULATIE_TELEFONIE", True)
SIMULATIE_WHATSAPP = _bool("SIMULATIE_WHATSAPP", True)
SIMULATIE_AGENDA = _bool("SIMULATIE_AGENDA", True)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Database met het actielog.
DB_PAD = os.getenv("DB_PAD", str(ROOT / "omnia.db"))
