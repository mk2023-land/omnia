"""Tests voor inkomende WhatsApp-berichten (webhook van Meta)."""

import hashlib
import hmac
import json

from fastapi.testclient import TestClient

import app.main as main

EIGENAAR = "31600000000"
PLANNER = "31611111111"
UITLEZING = {"merk": "Remeha", "type": None, "foutcode": "F28", "klacht": "Geen warm water",
             "spoed": True, "spoed_reden": "Geen warm water"}


def payload(van, tekst, msg_id):
    return {"entry": [{"changes": [{"value": {"messages": [
        {"from": van, "id": msg_id, "type": "text", "text": {"body": tekst}}]}}]}]}


def post(client, data):
    body = json.dumps(data).encode()
    sig = "sha256=" + hmac.new(b"testsecret", body, hashlib.sha256).hexdigest()
    return client.post("/whatsapp/webhook", content=body,
                       headers={"X-Hub-Signature-256": sig, "Content-Type": "application/json"})


def soorten(client):
    return [a["soort"] for a in client.get("/api/acties").json()]


def test_verificatie_door_meta():
    client = TestClient(main.app)
    ok = client.get("/whatsapp/webhook", params={"hub.mode": "subscribe", "hub.verify_token": "testverify", "hub.challenge": "42"})
    assert ok.status_code == 200 and ok.text == "42"
    fout = client.get("/whatsapp/webhook", params={"hub.mode": "subscribe", "hub.verify_token": "nep", "hub.challenge": "42"})
    assert fout.status_code == 403


def test_zonder_geldige_handtekening_geweigerd():
    client = TestClient(main.app)
    r = client.post("/whatsapp/webhook", json=payload(EIGENAAR, "ik ruik gas", "x1"), headers={"X-Hub-Signature-256": "sha256=nep"})
    assert r.status_code == 403


def test_eigenaar_is_demoklant_en_gas_werkt():
    client = TestClient(main.app)
    client.post("/api/reset")
    post(client, payload(EIGENAAR, "ik ruik gas", "gas-1"))
    acties = client.get("/api/acties").json()
    assert acties[0]["klant"] == "demo"
    assert "gasmelding" in soorten(client)


def test_dubbel_bericht_wordt_een_keer_verwerkt():
    client = TestClient(main.app)
    client.post("/api/reset")
    post(client, payload(EIGENAAR, "ik ruik gas", "dubbel-1"))
    post(client, payload(EIGENAAR, "ik ruik gas", "dubbel-1"))
    assert soorten(client).count("gasmelding") == 1


def test_onbekend_nummer_genegeerd():
    client = TestClient(main.app)
    client.post("/api/reset")
    post(client, payload("31699999999", "ketel stuk", "vreemd-1"))
    assert soorten(client) == ["niet_op_lijst"]


def test_planner_keurt_goed_met_1(monkeypatch):
    monkeypatch.setattr(main, "lees_uit", lambda t, f, m: dict(UITLEZING))
    client = TestClient(main.app)
    client.post("/api/reset")
    post(client, payload(EIGENAAR, "Remeha geeft F28", "klant-1"))
    assert "voorstel" in soorten(client) and "planner_uit" in soorten(client)
    post(client, payload(PLANNER, "1", "planner-1"))
    s = soorten(client)
    assert "goedkeuring" in s
    uit = [a for a in client.get("/api/acties").json() if a["soort"] == "bericht_uit"]
    assert "Goed nieuws" in uit[-1]["tekst"]


def test_planner_andere_tijd_en_onzin(monkeypatch):
    monkeypatch.setattr(main, "lees_uit", lambda t, f, m: dict(UITLEZING))
    client = TestClient(main.app)
    client.post("/api/reset")
    post(client, payload(EIGENAAR, "Remeha geeft F28", "klant-2"))
    post(client, payload(PLANNER, "2", "planner-2"))
    assert soorten(client).count("voorstel") == 2
    post(client, payload(PLANNER, "misschien", "planner-3"))
    laatste = client.get("/api/acties").json()[-1]
    assert laatste["soort"] == "planner_uit" and "1 (goedkeuren)" in laatste["tekst"]
    assert "goedkeuring" not in soorten(client)
