"""Tests voor de werkstroom rond US-2."""

import pytest
from fastapi.testclient import TestClient

from app.core.logboek import Logboek
from app.core.veiligheid import NOODNUMMER_GAS
from app.core.werkstroom import verwerk_bericht
from app.main import app


@pytest.fixture
def logboek(tmp_path):
    return Logboek(tmp_path / "log.db")


def ai_plat(_tekst):
    raise ConnectionError("AI-dienst niet bereikbaar")


def test_gas_krijgt_direct_noodnummer_en_plannermelding(logboek):
    uitkomst = verwerk_bericht(logboek, "klant1", "ik ruik gas")
    assert uitkomst["route"] == "gasmelding"

    uit = logboek.lees(soort="bericht_uit")
    assert len(uit) == 1 and NOODNUMMER_GAS in uit[0]["tekst"]

    meldingen = logboek.lees(soort="gasmelding")
    assert len(meldingen) == 1 and meldingen[0]["noodnummer"] == NOODNUMMER_GAS
    assert logboek.lees(soort="gewone_rij") == []


def test_gas_werkt_ook_als_ai_plat_ligt(logboek):
    uitkomst = verwerk_bericht(logboek, "klant1", "gaslucth in huis", ai_stap=ai_plat)
    assert uitkomst["route"] == "gasmelding"
    assert logboek.lees(soort="ai_fout") == []


def test_ai_wordt_bij_gas_niet_aangeroepen(logboek):
    aangeroepen = []
    verwerk_bericht(logboek, "klant1", "ik ruik gas", ai_stap=lambda t: aangeroepen.append(t) or {})
    assert aangeroepen == []


def test_gewone_storing_gaat_naar_gewone_rij(logboek):
    uitkomst = verwerk_bericht(logboek, "klant1", "ketel geeft F28")
    assert uitkomst["route"] == "gewone_rij"
    assert logboek.lees(soort="gasmelding") == []
    assert logboek.lees(soort="bericht_uit") == []


def test_ai_fout_bij_gewone_storing_wordt_gelogd(logboek):
    uitkomst = verwerk_bericht(logboek, "klant1", "ketel geeft F28", ai_stap=ai_plat)
    assert uitkomst["route"] == "gewone_rij"
    assert len(logboek.lees(soort="ai_fout")) == 1


def test_api_en_reset():
    client = TestClient(app)
    client.post("/api/reset")
    r = client.post("/api/bericht", json={"tekst": "ik ruik gas"})
    assert r.json()["route"] == "gasmelding"
    soorten = [a["soort"] for a in client.get("/api/acties").json()]
    assert soorten == ["bericht_in", "bericht_uit", "gasmelding"]
    client.post("/api/reset")
    assert client.get("/api/acties").json() == []
    for pad in ("/demo/gas", "/planner"):
        assert client.get(pad).status_code == 200


def test_echte_verzending_valt_terug_bij_fout(logboek, monkeypatch):
    from app import config
    from app.core import whatsapp

    def kapot(_naar, _tekst):
        raise whatsapp.WhatsAppFout("131047: buiten 24-uursvenster")

    monkeypatch.setattr(config, "SIMULATIE_WHATSAPP", False)
    monkeypatch.setattr(whatsapp, "stuur_tekst", kapot)
    uitkomst = verwerk_bericht(logboek, "demo", "ik ruik gas")
    assert uitkomst["route"] == "gasmelding"
    assert len(logboek.lees(soort="verzendfout")) == 1
    assert len(logboek.lees(soort="gasmelding")) == 1


def test_echte_verzending_gebruikt_testnummer_voor_demoklant(logboek, monkeypatch):
    from app import config
    from app.core import whatsapp

    verstuurd = []
    monkeypatch.setattr(config, "SIMULATIE_WHATSAPP", False)
    monkeypatch.setattr(config, "WHATSAPP_TEST_ONTVANGER", "+31600000000")
    monkeypatch.setattr(whatsapp, "stuur_tekst", lambda naar, tekst: verstuurd.append(naar) or "wamid.test")
    verwerk_bericht(logboek, "demo", "ik ruik gas")
    assert verstuurd == ["+31600000000"]


def test_demoscherm_en_rekensom_api():
    client = TestClient(app)
    assert client.get("/demo").status_code == 200
    r = client.get("/api/rekensom", params={"oproepen_per_week": 60, "deel_gemist_pct": 25, "waarde_klus": 250})
    assert r.status_code == 200 and r.json()["omzet_per_maand"] > 0
    fout = client.get("/api/rekensom", params={"oproepen_per_week": 60, "deel_gemist_pct": 150, "waarde_klus": 250})
    assert fout.status_code == 422
