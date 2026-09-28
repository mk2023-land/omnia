"""Berichten naar de klant sturen.

In simulatie wordt het bericht alleen gelogd en verschijnt het op de demotelefoon
in de browser. Met SIMULATIE_WHATSAPP=false gaat het ook echt via WhatsApp.
"""

from app import config
from app.core import sms, whatsapp
from app.core.logboek import Logboek

# De klant op de demopagina heet "demo"; in het echt is dat het testnummer.
DEMO_KLANT = "demo"


def telefoonnummer(klant: str) -> str:
    return config.WHATSAPP_TEST_ONTVANGER if klant == DEMO_KLANT else klant


def verstuur(logboek: Logboek, naar: str, tekst: str, kanaal: str = "whatsapp") -> dict:
    if config.SIMULATIE_WHATSAPP:
        return logboek.schrijf(naar, "bericht_uit", tekst=tekst, kanaal=kanaal, gesimuleerd=True)

    # Echt versturen. Mislukt dat, dan loggen we de fout maar gaat de werkstroom door:
    # het bericht staat dan in elk geval op het plannerscherm.
    try:
        bericht_id = whatsapp.stuur_tekst(telefoonnummer(naar), tekst)
    except (whatsapp.WhatsAppFout, OSError) as fout:
        logboek.schrijf(naar, "verzendfout", kanaal=kanaal, fout=str(fout))
        return logboek.schrijf(naar, "bericht_uit", tekst=tekst, kanaal=kanaal, gesimuleerd=False, verzonden=False)
    return logboek.schrijf(
        naar, "bericht_uit", tekst=tekst, kanaal=kanaal, gesimuleerd=False, verzonden=True, bericht_id=bericht_id
    )


def verstuur_sms(logboek: Logboek, klant: str, nummer: str, tekst: str) -> dict:
    if config.SIMULATIE_TELEFONIE:
        return logboek.schrijf(klant, "bericht_uit", tekst=tekst, kanaal="sms", gesimuleerd=True)
    try:
        sid = sms.stuur(nummer, tekst)
    except (sms.SmsFout, OSError) as fout:
        logboek.schrijf(klant, "verzendfout", kanaal="sms", fout=str(fout))
        return logboek.schrijf(klant, "bericht_uit", tekst=tekst, kanaal="sms", gesimuleerd=False, verzonden=False)
    return logboek.schrijf(klant, "bericht_uit", tekst=tekst, kanaal="sms", gesimuleerd=False, verzonden=True, bericht_id=sid)


def meld_planner(logboek: Logboek, tekst: str) -> dict | None:
    """Bericht naar de planner-telefoon (tweede demotelefoon). Doet niets als die niet is ingesteld."""
    if not config.PLANNER_NUMMER:
        return None
    if config.SIMULATIE_WHATSAPP:
        return logboek.schrijf("planner", "planner_uit", tekst=tekst, gesimuleerd=True)
    try:
        whatsapp.stuur_tekst(config.PLANNER_NUMMER, tekst)
    except (whatsapp.WhatsAppFout, OSError) as fout:
        return logboek.schrijf("planner", "verzendfout", kanaal="whatsapp", fout=f"Planner: {fout}")
    return logboek.schrijf("planner", "planner_uit", tekst=tekst, gesimuleerd=False)
