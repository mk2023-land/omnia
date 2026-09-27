"""Sms en belverzoeken via Twilio (US-1).

Geen extra pakket nodig: de Twilio REST API is een gewone HTTP-aanroep.
"""

import base64
import hashlib
import hmac

import httpx

from app import config


class SmsFout(Exception):
    pass


def stuur(naar: str, tekst: str) -> str:
    if not (config.TWILIO_ACCOUNT_SID and config.TWILIO_AUTH_TOKEN and config.TWILIO_NUMMER):
        raise SmsFout("Twilio-gegevens ontbreken in .env")
    r = httpx.post(
        f"https://api.twilio.com/2010-04-01/Accounts/{config.TWILIO_ACCOUNT_SID}/Messages.json",
        auth=(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN),
        data={"To": naar, "From": config.TWILIO_NUMMER, "Body": tekst},
        timeout=15,
    )
    data = r.json()
    if r.status_code >= 400:
        raise SmsFout(f"{data.get('code')}: {data.get('message')}")
    return data["sid"]


def handtekening_klopt(url: str, velden: dict[str, str], handtekening: str) -> bool:
    """Controleert of een webhook echt van Twilio komt (X-Twilio-Signature)."""
    if not config.TWILIO_AUTH_TOKEN:
        return False
    tekst = url + "".join(k + velden[k] for k in sorted(velden))
    verwacht = base64.b64encode(hmac.new(config.TWILIO_AUTH_TOKEN.encode(), tekst.encode(), hashlib.sha1).digest()).decode()
    return hmac.compare_digest(verwacht, handtekening or "")
