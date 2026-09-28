"""Inkomende WhatsApp-berichten (webhook van Meta).

- De eigenaar (eerste testontvanger) speelt de klant: zijn berichten gaan de werkstroom in
  als klant "demo", zodat ze ook op de demoschermen verschijnen.
- De tweede demotelefoon (PLANNER_NUMMER) is de planner: die antwoordt 1, 2 of 3 op een voorstel.
- Andere nummers worden genegeerd.
"""

import hashlib
import hmac

import httpx

from app import config
from app.core import berichten, planning, whatsapp
from app.core.agenda import Agenda
from app.core.logboek import Logboek
from app.core.terugbellen import mag_ontvangen
from app.core.werkstroom import AiStap, ai_uitlezen, verwerk_bericht

KEUZES = {
    "1": "goedkeuren", "ja": "goedkeuren", "goedkeuren": "goedkeuren", "ok": "goedkeuren",
    "2": "andere-tijd", "andere tijd": "andere-tijd", "anders": "andere-tijd",
    "3": "zelf-bellen", "zelf bellen": "zelf-bellen", "bellen": "zelf-bellen",
}

# Meta stuurt een bericht soms twee keer; zo verwerken we het maar één keer.
_gezien: set[str] = set()


def kaal(nummer: str) -> str:
    return "".join(t for t in nummer if t.isdigit())


def handtekening_klopt(body: bytes, handtekening: str) -> bool:
    """Controleert X-Hub-Signature-256 met het app secret."""
    if not config.WHATSAPP_APP_SECRET:
        return False
    verwacht = "sha256=" + hmac.new(config.WHATSAPP_APP_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(verwacht, handtekening or "")


def klant_voor(nummer: str) -> str:
    """De eigenaar heet in OMNIA 'demo', zodat de demoschermen zijn berichten tonen."""
    return berichten.DEMO_KLANT if kaal(nummer) == kaal(config.TESTONTVANGERS[0]) else nummer


def download_foto(media_id: str) -> tuple[bytes, str]:
    headers = {"Authorization": f"Bearer {config.WHATSAPP_TOKEN}"}
    info = httpx.get(f"https://graph.facebook.com/{config.WHATSAPP_API_VERSIE}/{media_id}", headers=headers, timeout=15).json()
    if "url" not in info:
        raise whatsapp.WhatsAppFout(f"Foto niet op te halen: {info.get('error', {}).get('message')}")
    r = httpx.get(info["url"], headers=headers, timeout=30)
    r.raise_for_status()
    return r.content, info.get("mime_type", "image/jpeg")


def berichten_uit(payload: dict) -> list[dict]:
    """Haalt de losse berichten uit de webhook-payload van Meta."""
    uit = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for m in change.get("value", {}).get("messages", []):
                uit.append(m)
    return uit


def verwerk(payload: dict, logboek: Logboek, agenda: Agenda, ai_stap: AiStap, foto_opslaan) -> None:
    for m in berichten_uit(payload):
        if m.get("id") in _gezien:
            continue
        _gezien.add(m.get("id"))
        nummer = "+" + kaal(m.get("from", ""))

        tekst = ""
        if m.get("type") == "text":
            tekst = m["text"].get("body", "")
        elif m.get("type") == "image":
            tekst = m["image"].get("caption", "")
        elif m.get("type") == "button":
            tekst = m["button"].get("text", "")

        # De planner-telefoon keurt voorstellen goed.
        if config.PLANNER_NUMMER and kaal(nummer) == kaal(config.PLANNER_NUMMER):
            planner_antwoord(logboek, agenda, tekst)
            continue

        if not mag_ontvangen(nummer):
            logboek.schrijf(nummer, "niet_op_lijst", nummer=nummer, reden="Bericht van nummer buiten de testlijst genegeerd.")
            continue

        foto, media_type, foto_url = None, "image/jpeg", None
        if m.get("type") == "image":
            try:
                ruw, _ = download_foto(m["image"]["id"])
                foto, media_type, foto_url = foto_opslaan(ruw)
            except Exception as fout:  # noqa: BLE001 - dan gaat alleen de tekst door
                logboek.schrijf(klant_voor(nummer), "verzendfout", kanaal="whatsapp", fout=f"Foto ophalen mislukt: {fout}")

        if not tekst and foto is None:
            continue
        klant = klant_voor(nummer)
        uitkomst = verwerk_bericht(logboek, klant, tekst, foto=foto, media_type=media_type, foto_url=foto_url)
        if uitkomst["route"] == "gewone_rij":
            ai_uitlezen(logboek, klant, tekst, foto, media_type, ai_stap, uitkomst["melding_id"], agenda)


def planner_antwoord(logboek: Logboek, agenda: Agenda, tekst: str) -> None:
    keuze = KEUZES.get(tekst.strip().lower().rstrip(".!"))
    voorstel = planning.open_voorstel(logboek)
    if keuze is None or voorstel is None:
        uitleg = "Er staat geen voorstel open." if voorstel is None else "Antwoord 1 (goedkeuren), 2 (andere tijd) of 3 (zelf bellen)."
        berichten.meld_planner(logboek, uitleg)
        return
    try:
        if keuze == "goedkeuren":
            planning.keur_goed(logboek, agenda, voorstel["id"])
            berichten.meld_planner(logboek, "✓ Ingepland. De klant heeft tijd en monteur gekregen.")
        elif keuze == "andere-tijd":
            planning.andere_tijd(logboek, agenda, voorstel["id"])  # stuurt zelf het nieuwe voorstel
        else:
            planning.zelf_bellen(logboek, voorstel["id"])
            berichten.meld_planner(logboek, "Genoteerd: je belt de klant zelf. Er is niets naar de klant gestuurd.")
    except planning.PlanningFout as fout:
        berichten.meld_planner(logboek, str(fout))
