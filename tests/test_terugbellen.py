"""Tests voor US-1: demonummer neemt niet op en stuurt een bericht."""

import base64
import hashlib
import hmac

import pytest
from fastapi.testclient import TestClient

import app.main as main
from app import config
from app.core import sms, whatsapp
from app.core.logboek import Logboek
from app.core.terugbellen import eerste_bericht, gemiste_oproep

EIGENAAR = "+31600000000"


@pytest.fixture
def log(tmp_path):
    return Logboek(tmp_path / "log.db")


def test_bericht_vraagt_alles_en_gebruikt_bedrijfsnaam():
    tekst = eerste_bericht("Loodgieter Jansen")
    for woord in ("merk", "type", "foutcode", "typeplaatje", "Loodgieter Jansen"):
        assert woord in tekst


def test_gemiste_oproep_stuurt_whatsapp(log):
    gemiste_oproep(log, "demo", EIGENAAR)
    uit = log.lees(soort="bericht_uit")
    assert len(uit) == 1 and uit[0]["kanaal"] == "whatsapp"
    assert log.lees(soort="oproep_gemist")[0]["nummer"] == EIGENAAR


def test_valt_terug_op_sms(log):
    gemiste_oproep(log, "demo", EIGENAAR, whatsapp_werkt=False)
    assert [a["kanaal"] for a in log.lees(soort="bericht_uit")] == ["sms"]
    assert len(log.lees(soort="verzendfout")) == 1


def test_echte_whatsapp_fout_valt_terug_op_sms(log, monkeypatch):
    def kapot(*_args, **_kw):
        raise whatsapp.WhatsAppFout("sjabloon nog niet goedgekeurd")

    monkeypatch.setattr(config, "SIMULATIE_WHATSAPP", False)
    monkeypatch.setattr(whatsapp, "stuur_sjabloon", kapot)
    gemiste_oproep(log, "demo", EIGENAAR)
    assert log.lees(soort="bericht_uit")[0]["kanaal"] == "sms"


def test_echte_whatsapp_gebruikt_sjabloon_met_bedrijfsnaam(log, monkeypatch):
    verstuurd = []
    monkeypatch.setattr(config, "SIMULATIE_WHATSAPP", False)
    monkeypatch.setattr(whatsapp, "stuur_sjabloon", lambda *a: verstuurd.append(a) or "wamid.x")
    gemiste_oproep(log, "demo", EIGENAAR)
    assert verstuurd == [(EIGENAAR, "omnia_gemiste_oproep", "nl", [config.BEDRIJFSNAAM])]


def test_onbekend_nummer_krijgt_niets(log):
    gemiste_oproep(log, "x", "+31699999999")
    assert log.lees(soort="bericht_uit") == []
    assert len(log.lees(soort="niet_op_lijst")) == 1


def test_nummer_mag_met_spaties(log):
    gemiste_oproep(log, "demo", "+31 6 0000 0000")
    assert len(log.lees(soort="bericht_uit")) == 1


# ---------- Twilio-webhook ----------

def handtekening(url, velden):
    tekst = url + "".join(k + velden[k] for k in sorted(velden))
    return base64.b64encode(hmac.new(b"testtoken", tekst.encode(), hashlib.sha1).digest()).decode()


def test_webhook_weigert_zonder_geldige_handtekening():
    client = TestClient(main.app)
    r = client.post("/twilio/voice", data={"From": EIGENAAR}, headers={"X-Twilio-Signature": "nep"})
    assert r.status_code == 403


def test_webhook_neemt_niet_op_en_stuurt_bericht():
    client = TestClient(main.app)
    client.post("/api/reset")
    velden = {"From": EIGENAAR, "To": "+3197000000", "CallSid": "CA123"}
    r = client.post("/twilio/voice", data=velden,
                    headers={"X-Twilio-Signature": handtekening("https://omnia.test/twilio/voice", velden)})
    assert r.status_code == 200 and "<Reject" in r.text
    soorten = [a["soort"] for a in client.get("/api/acties").json()]
    assert soorten == ["oproep_gemist", "bericht_uit"]


def test_handtekening_zonder_token_faalt(monkeypatch):
    monkeypatch.setattr(config, "TWILIO_AUTH_TOKEN", "")
    assert not sms.handtekening_klopt("https://x", {}, "iets")


def test_demoknop_api():
    client = TestClient(main.app)
    client.post("/api/reset")
    client.post("/api/oproep", data={"whatsapp_werkt": "false"})
    uit = [a for a in client.get("/api/acties").json() if a["soort"] == "bericht_uit"]
    assert uit[0]["kanaal"] == "sms"
    client.post("/api/reset")
    client.post("/api/oproep", data={"onbekend": "true"})
    assert [a["soort"] for a in client.get("/api/acties").json()] == ["oproep_gemist", "niet_op_lijst"]
