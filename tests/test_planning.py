"""Tests voor US-4: planningsvoorstel met goedkeuring."""

from datetime import date, datetime, time

import pytest
from fastapi.testclient import TestClient

import app.main as main
from app.core import planning
from app.core.agenda import BLOKKEN, MONTEURS, Agenda, Blok, nette_tijd, werkdagen
from app.core.logboek import Logboek
from app.core.werkstroom import verwerk_bericht

MAANDAG = date(2026, 9, 28)
UITLEZING = {"merk": "Remeha", "type": None, "foutcode": "F28", "klacht": "Geen warm water",
             "spoed": True, "spoed_reden": "Geen warm water"}


@pytest.fixture
def log(tmp_path):
    return Logboek(tmp_path / "db.sqlite")


@pytest.fixture
def agenda(tmp_path):
    a = Agenda(tmp_path / "db.sqlite")
    a.vul_demo_week(MAANDAG)
    return a


def voorstel(log, agenda, spoed=True, nu=datetime(2026, 9, 28, 9, 0)):
    melding = log.schrijf("klant1", "gewone_rij", tekst="F28")
    return planning.maak_voorstel(log, agenda, "klant1", melding["id"], {**UITLEZING, "spoed": spoed}, nu=nu)


# ---------- Agenda ----------

def test_demo_week_is_gevuld_maar_niet_vol(agenda):
    aantal = len(agenda.afspraken(MAANDAG, 7))
    totaal = 5 * len(MONTEURS) * len(BLOKKEN)
    assert 0.5 * totaal < aantal < totaal


def test_demo_week_is_altijd_hetzelfde(tmp_path, agenda):
    ander = Agenda(tmp_path / "ander.sqlite")
    ander.vul_demo_week(MAANDAG)
    zonder_id = lambda rijen: [{k: v for k, v in r.items() if k != "id"} for r in rijen]  # noqa: E731
    assert zonder_id(ander.afspraken(MAANDAG)) == zonder_id(agenda.afspraken(MAANDAG))


def test_werkdagen_slaan_weekend_over():
    assert [d.weekday() for d in werkdagen(date(2026, 10, 2), 3)] == [4, 0, 1]


def test_nette_tijd():
    assert nette_tijd(datetime(2026, 9, 29, 10), datetime(2026, 9, 29, 12)) == "dinsdag 29 september, 10:00–12:00"


def test_bezet_blok_kan_niet_dubbel(agenda):
    blok = agenda.vrije_blokken(datetime(2026, 9, 28, 0, 0), 1)[0]
    agenda.plan(blok, "test")
    with pytest.raises(ValueError):
        agenda.plan(blok, "nog een keer")


# ---------- Voorstel ----------

def test_spoed_krijgt_eerste_vrije_blok_na_nu(log, agenda):
    v = voorstel(log, agenda, spoed=True)
    assert datetime.fromisoformat(v["start"]) > datetime(2026, 9, 28, 9, 0)
    assert agenda.is_vrij(Blok(v["monteur"], datetime.fromisoformat(v["start"]), datetime.fromisoformat(v["eind"])))


def test_geen_spoed_begint_morgen(log, agenda):
    v = voorstel(log, agenda, spoed=False)
    assert datetime.fromisoformat(v["start"]).date() > MAANDAG


def test_voorstel_stuurt_niets_naar_klant(log, agenda):
    voorstel(log, agenda)
    assert log.lees(soort="bericht_uit") == []


def test_goedkeuren_plant_en_bericht_aan_klant(log, agenda):
    v = voorstel(log, agenda)
    planning.keur_goed(log, agenda, v["id"])
    uit = log.lees(soort="bericht_uit")
    assert len(uit) == 1 and v["monteur"] in uit[0]["tekst"] and v["tijd_tekst"] in uit[0]["tekst"]
    assert not agenda.is_vrij(Blok(v["monteur"], datetime.fromisoformat(v["start"]), datetime.fromisoformat(v["eind"])))


def test_dubbel_goedkeuren_kan_niet(log, agenda):
    v = voorstel(log, agenda)
    planning.keur_goed(log, agenda, v["id"])
    with pytest.raises(planning.PlanningFout):
        planning.keur_goed(log, agenda, v["id"])
    assert len(log.lees(soort="bericht_uit")) == 1


def test_andere_tijd_geeft_later_blok_en_oud_voorstel_is_dicht(log, agenda):
    v = voorstel(log, agenda)
    nieuw = planning.andere_tijd(log, agenda, v["id"])
    assert nieuw["soort"] == "voorstel" and nieuw["start"] > v["start"]
    with pytest.raises(planning.PlanningFout):
        planning.keur_goed(log, agenda, v["id"])
    assert log.lees(soort="bericht_uit") == []


def test_zelf_bellen_stuurt_niets(log, agenda):
    v = voorstel(log, agenda)
    planning.zelf_bellen(log, v["id"])
    assert log.lees(soort="bericht_uit") == []


def test_volle_agenda_geeft_geen_voorstel(log, agenda):
    for blok in agenda.vrije_blokken(datetime(2026, 9, 28, 0, 0), aantal=500):
        agenda.plan(blok, "vol")
    assert voorstel(log, agenda)["soort"] == "geen_voorstel"


# ---------- Werkstroom en API ----------

def test_werkstroom_maakt_voorstel_na_ai(log, agenda):
    verwerk_bericht(log, "klant1", "F28", ai_stap=lambda t, f, m: dict(UITLEZING), agenda=agenda)
    assert len(log.lees(soort="voorstel")) == 1


def test_gas_krijgt_geen_voorstel(log, agenda):
    verwerk_bericht(log, "klant1", "ik ruik gas", ai_stap=lambda t, f, m: dict(UITLEZING), agenda=agenda)
    assert log.lees(soort="voorstel") == []


def test_api_goedkeuren_en_foute_keuzes(monkeypatch):
    monkeypatch.setattr(main, "lees_uit", lambda t, f, m: dict(UITLEZING))
    client = TestClient(main.app)
    client.post("/api/reset")
    client.post("/api/bericht", data={"tekst": "F28"})
    v = next(a for a in client.get("/api/acties").json() if a["soort"] == "voorstel")
    assert client.post(f"/api/voorstel/{v['id']}/onzin").status_code == 404
    assert client.post(f"/api/voorstel/{v['id']}/goedkeuren").status_code == 200
    assert client.post(f"/api/voorstel/{v['id']}/goedkeuren").status_code == 409
    agenda = client.get("/api/agenda").json()
    assert any(a["soort"] == "gepland" for a in agenda["afspraken"])
