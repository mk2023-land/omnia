"""Tests voor US-3 zonder de echte AI aan te roepen."""

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import app.main as main
from app.core import fotos
from app.core.logboek import Logboek
from app.core.uitlezen import UitleesFout, Uitlezing, controleer
from app.core.werkstroom import bevestiging, verwerk_bericht

VOORBEELD = {"merk": "Remeha", "type": "Calenta Ace 28C", "foutcode": "H02.02",
             "klacht": "Geen warm water", "spoed": True, "spoed_reden": "Geen warm water"}


def uitlezing(**anders) -> Uitlezing:
    return Uitlezing(**{**VOORBEELD, **anders})


def jpeg(breed=200, hoog=100) -> bytes:
    uit = io.BytesIO()
    Image.new("RGB", (breed, hoog), (200, 200, 200)).save(uit, format="JPEG")
    return uit.getvalue()


# ---------- Controle van de AI-uitvoer ----------

@pytest.mark.parametrize("gok", ["onbekend", "Onbekend.", "n.v.t.", "?", "", "   ", "niet leesbaar"])
def test_gokwaarden_worden_leeg(gok):
    schoon = controleer(uitlezing(merk=gok, type=gok, foutcode=gok))
    assert schoon["merk"] is None and schoon["type"] is None and schoon["foutcode"] is None


def test_merk_en_foutcode_worden_netjes():
    schoon = controleer(uitlezing(merk="remeha", foutcode="f28"))
    assert schoon["merk"] == "Remeha"
    assert schoon["foutcode"] == "F28"


def test_vreemde_foutcode_wordt_leeg():
    assert controleer(uitlezing(foutcode="F28; drop table"))["foutcode"] is None


def test_spoed_zonder_reden_wordt_afgekeurd():
    with pytest.raises(UitleesFout):
        controleer(uitlezing(spoed_reden="  "))


def test_bevestiging_vraagt_om_typeplaatje_als_type_ontbreekt():
    tekst = bevestiging({**VOORBEELD, "type": None})
    assert "typeplaatje" in tekst and "type" in tekst
    assert "typeplaatje" not in bevestiging(VOORBEELD)


# ---------- Werkstroom ----------

def test_ai_uitvoer_wordt_gelogd_en_bevestigd(tmp_path):
    log = Logboek(tmp_path / "log.db")
    verwerk_bericht(log, "klant1", "ketel geeft H02.02", ai_stap=lambda t, f, m: dict(VOORBEELD))
    assert log.lees(soort="ai_uitvoer")[0]["foutcode"] == "H02.02"
    assert "Bedankt" in log.lees(soort="bericht_uit")[0]["tekst"]


def test_foto_gaat_mee_naar_de_ai(tmp_path):
    log = Logboek(tmp_path / "log.db")
    ontvangen = []
    verwerk_bericht(log, "klant1", "", foto=b"beeld", ai_stap=lambda t, f, m: ontvangen.append(f) or dict(VOORBEELD))
    assert ontvangen == [b"beeld"]


# ---------- Foto's ----------

def test_grote_foto_wordt_verkleind(tmp_path):
    data, media_type, naam = fotos.verwerk(jpeg(4000, 3000), tmp_path)
    assert media_type == "image/jpeg" and (tmp_path / naam).exists()
    assert max(Image.open(io.BytesIO(data)).size) == fotos.MAX_ZIJDE


def test_geen_foto_wordt_geweigerd(tmp_path):
    with pytest.raises(fotos.FotoFout):
        fotos.verwerk(b"dit is geen foto", tmp_path)


# ---------- API ----------

def test_api_met_foto_draait_ai_op_achtergrond(monkeypatch):
    monkeypatch.setattr(main, "lees_uit", lambda t, f, m: dict(VOORBEELD))
    client = TestClient(main.app)
    client.post("/api/reset")
    r = client.post("/api/bericht", data={"tekst": "doet het niet"},
                    files={"foto": ("ketel.jpg", jpeg(), "image/jpeg")})
    assert r.json()["route"] == "gewone_rij"
    acties = client.get("/api/acties").json()
    assert [a["soort"] for a in acties] == ["bericht_in", "gewone_rij", "ai_uitvoer", "bericht_uit"]
    assert client.get(acties[0]["foto_url"]).status_code == 200


def test_api_zonder_sleutel_logt_ai_fout():
    client = TestClient(main.app)
    client.post("/api/reset")
    client.post("/api/bericht", data={"tekst": "ketel geeft F28"})
    assert "ANTHROPIC_API_KEY" in client.get("/api/acties").json()[-1]["fout"]


def test_api_weigert_leeg_bericht_en_kapotte_foto():
    client = TestClient(main.app)
    assert client.post("/api/bericht", data={"tekst": " "}).status_code == 422
    r = client.post("/api/bericht", files={"foto": ("x.jpg", b"kapot", "image/jpeg")})
    assert r.status_code == 422
