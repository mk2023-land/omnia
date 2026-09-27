"""Berichten naar de klant sturen.

In simulatie wordt het bericht alleen gelogd en verschijnt het op de demotelefoon
in de browser. Zodra de WhatsApp Cloud API klaarstaat (US-1), komt hier de echte
verzending bij.
"""

from app import config
from app.core.logboek import Logboek


def verstuur(logboek: Logboek, naar: str, tekst: str, kanaal: str = "whatsapp") -> dict:
    if not config.SIMULATIE_WHATSAPP:
        raise NotImplementedError("Echte WhatsApp-verzending volgt in US-1.")
    return logboek.schrijf(naar, "bericht_uit", tekst=tekst, kanaal=kanaal, gesimuleerd=True)
