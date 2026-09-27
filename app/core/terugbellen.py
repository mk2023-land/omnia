"""US-1: het demonummer neemt niet op en stuurt binnen een minuut een bericht.

Eerst WhatsApp (goedgekeurd sjabloon), lukt dat niet dan een sms. Alleen nummers
op de lijst van testontvangers krijgen iets: dat is ook wat het testnummer van Meta afdwingt.
"""

from app import config
from app.core import berichten, whatsapp
from app.core.logboek import Logboek

SJABLOON = "omnia_gemiste_oproep"


def eerste_bericht(bedrijfsnaam: str) -> str:
    """Moet gelijk blijven aan het sjabloon dat bij Meta is ingediend."""
    return (
        f"Hallo, u belde net met {bedrijfsnaam} en we konden helaas niet opnemen. "
        "Zo helpen we u sneller: stuur hier het merk en type van uw ketel, de foutcode op het display "
        "en een foto van het typeplaatje. We nemen daarna zo snel mogelijk contact met u op."
    )


def mag_ontvangen(nummer: str) -> bool:
    kaal = lambda n: "".join(t for t in n if t.isdigit())  # noqa: E731
    return kaal(nummer) in {kaal(n) for n in config.TESTONTVANGERS}


def gemiste_oproep(logboek: Logboek, klant: str, nummer: str, whatsapp_werkt: bool = True) -> dict:
    """Verwerkt een gemiste oproep. `whatsapp_werkt=False` bootst in de demo de sms-terugval na."""
    logboek.schrijf(klant, "oproep_gemist", nummer=nummer)
    if not mag_ontvangen(nummer):
        return logboek.schrijf(klant, "niet_op_lijst", nummer=nummer,
                               reden="Nummer staat niet op de lijst van testontvangers; er is niets verstuurd.")

    tekst = eerste_bericht(config.BEDRIJFSNAAM)

    # 1. WhatsApp met het goedgekeurde sjabloon.
    fout = None
    if not whatsapp_werkt:
        fout = "WhatsApp niet beschikbaar (nagebootst)"
    elif config.SIMULATIE_WHATSAPP:
        return logboek.schrijf(klant, "bericht_uit", tekst=tekst, kanaal="whatsapp", gesimuleerd=True)
    else:
        try:
            bericht_id = whatsapp.stuur_sjabloon(nummer, SJABLOON, "nl", [config.BEDRIJFSNAAM])
            return logboek.schrijf(klant, "bericht_uit", tekst=tekst, kanaal="whatsapp", gesimuleerd=False,
                                   verzonden=True, bericht_id=bericht_id)
        except (whatsapp.WhatsAppFout, OSError) as e:
            fout = str(e)

    # 2. Terugval: sms.
    logboek.schrijf(klant, "verzendfout", kanaal="whatsapp", fout=fout)
    return berichten.verstuur_sms(logboek, klant, nummer, tekst)

