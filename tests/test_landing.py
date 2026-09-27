from fastapi.testclient import TestClient

from app.main import app
from app.stories import BOUWVOLGORDE, STATUSSEN, STORIES

client = TestClient(app)


def test_landingspagina_toont_alle_stories():
    r = client.get("/")
    assert r.status_code == 200
    for s in STORIES:
        assert s.code in r.text
        assert s.titel in r.text


def test_statussen_en_bouwvolgorde_kloppen():
    codes = {s.code for s in STORIES}
    assert set(BOUWVOLGORDE) == codes
    assert all(s.status in STATUSSEN for s in STORIES)


def test_logo_wordt_geserveerd():
    assert client.get("/static/img/omnia-logo.webp").status_code == 200
