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

# WhatsApp Cloud API (zie docs/accounts.md)
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_BUSINESS_ACCOUNT_ID = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "")
WHATSAPP_APP_SECRET = os.getenv("WHATSAPP_APP_SECRET", "")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
WHATSAPP_TEST_ONTVANGER = os.getenv("WHATSAPP_TEST_ONTVANGER", "")
WHATSAPP_API_VERSIE = os.getenv("WHATSAPP_API_VERSIE", "v23.0")

# Database met het actielog.
DB_PAD = os.getenv("DB_PAD", str(ROOT / "omnia.db"))
