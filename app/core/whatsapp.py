"""Koppeling met de WhatsApp Cloud API van Meta.

Gebruikt het testnummer van Meta: dat stuurt alleen naar vooraf opgegeven nummers.
Een vrij tekstbericht komt alleen aan binnen 24 uur nadat de klant zelf iets
stuurde; daarbuiten is een goedgekeurd sjabloon nodig.
"""

import httpx

from app import config


class WhatsAppFout(Exception):
    pass


def _url(pad: str) -> str:
    return f"https://graph.facebook.com/{config.WHATSAPP_API_VERSIE}/{pad}"


def _headers() -> dict:
    if not config.WHATSAPP_TOKEN:
        raise WhatsAppFout("WHATSAPP_TOKEN ontbreekt in .env")
    return {"Authorization": f"Bearer {config.WHATSAPP_TOKEN}"}


def _nummer(naar: str) -> str:
    """'+31 6 1234 5678' -> '31612345678', zoals de API het wil."""
    return "".join(t for t in naar if t.isdigit())


def _post(payload: dict) -> dict:
    r = httpx.post(
        _url(f"{config.WHATSAPP_PHONE_NUMBER_ID}/messages"),
        headers=_headers(),
        json={"messaging_product": "whatsapp", **payload},
        timeout=15,
    )
    data = r.json()
    if r.status_code >= 400 or "error" in data:
        fout = data.get("error", {})
        raise WhatsAppFout(f"{fout.get('code')}: {fout.get('message')} ({fout.get('error_data', {}).get('details', '')})")
    return data


def stuur_tekst(naar: str, tekst: str) -> str:
    """Vrij tekstbericht. Geeft het bericht-ID van Meta terug."""
    data = _post({"to": _nummer(naar), "type": "text", "text": {"body": tekst}})
    return data["messages"][0]["id"]


def stuur_sjabloon(naar: str, naam: str, taal: str = "nl", parameters: list[str] | None = None) -> str:
    """Goedgekeurd sjabloon, eventueel met {{1}}, {{2}}... ingevuld."""
    sjabloon: dict = {"name": naam, "language": {"code": taal}}
    if parameters:
        sjabloon["components"] = [
            {"type": "body", "parameters": [{"type": "text", "text": p} for p in parameters]}
        ]
    data = _post({"to": _nummer(naar), "type": "template", "template": sjabloon})
    return data["messages"][0]["id"]


def controleer_verbinding() -> dict:
    """Vraagt de gegevens van het testnummer op; faalt als token of ID niet klopt."""
    r = httpx.get(
        _url(config.WHATSAPP_PHONE_NUMBER_ID),
        headers=_headers(),
        params={"fields": "display_phone_number,verified_name,quality_rating"},
        timeout=15,
    )
    data = r.json()
    if "error" in data:
        raise WhatsAppFout(data["error"].get("message"))
    return data
