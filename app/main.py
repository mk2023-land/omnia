"""OMNIA-demo: webserver voor de landingspagina en de demo's per user story.

Starten:  .venv\\Scripts\\python -m uvicorn app.main:app --reload
"""

from datetime import date
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app import config
from app.core import fotos, planning, rekensom
from app.core.agenda import BLOKKEN, MONTEURS, Agenda, werkdagen
from app.core.logboek import Logboek
from app.core.uitlezen import lees_uit
from app.core.werkstroom import ai_uitlezen, verwerk_bericht
from app.stories import BOUWVOLGORDE, STORIES
from app.voorbeelden import GROEPEN

APP_DIR = Path(__file__).resolve().parent

app = FastAPI(title="OMNIA-demo")
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")
FOTO_MAP = config.ROOT / "data" / "fotos"
FOTO_MAP.mkdir(parents=True, exist_ok=True)
app.mount("/fotos", StaticFiles(directory=FOTO_MAP), name="fotos")
templates = Jinja2Templates(directory=APP_DIR / "templates")

# Versienummer achter CSS en JS, zodat de browser nooit een oude versie gebruikt.
def _css_versie() -> int:
    return int(max(p.stat().st_mtime for p in (APP_DIR / "static").rglob("*.*s")))


templates.env.globals["css_versie"] = _css_versie
app.state.logboek = Logboek(config.DB_PAD)
app.state.agenda = Agenda(config.DB_PAD)
if app.state.agenda.is_leeg():
    app.state.agenda.vul_demo_week()


def logboek(request: Request) -> Logboek:
    return request.app.state.logboek


def agenda(request: Request) -> Agenda:
    return request.app.state.agenda


# ---------- Pagina's ----------

@app.get("/", response_class=HTMLResponse)
def landingspagina(request: Request):
    klaar = sum(1 for s in STORIES if s.status in {"gesimuleerd", "live"})
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "stories": STORIES,
            "bouwvolgorde": BOUWVOLGORDE,
            "klaar": klaar,
            "bedrijfsnaam": config.BEDRIJFSNAAM,
        },
    )


@app.get("/demo", response_class=HTMLResponse)
def demoscherm(request: Request):
    return templates.TemplateResponse(
        request, "demoscherm.html", {"bedrijfsnaam": config.BEDRIJFSNAAM, "voorbeeld": rekensom.VOORBEELD}
    )


@app.get("/demo/telefoon", response_class=HTMLResponse)
@app.get("/demo/gas", response_class=HTMLResponse)
def demotelefoon(request: Request):
    return templates.TemplateResponse(
        request, "telefoon.html", {"bedrijfsnaam": config.BEDRIJFSNAAM, "met_telefoon": True, "groepen": GROEPEN}
    )


@app.get("/planner", response_class=HTMLResponse)
def planner(request: Request):
    return templates.TemplateResponse(
        request, "telefoon.html", {"bedrijfsnaam": config.BEDRIJFSNAAM, "met_telefoon": False}
    )


@app.get("/agenda", response_class=HTMLResponse)
def agenda_pagina(request: Request):
    blokken = [(van.strftime("%H:%M"), tot.strftime("%H:%M")) for van, tot in BLOKKEN]
    return templates.TemplateResponse(
        request, "agenda.html", {"blokken": blokken, "simulatie": config.SIMULATIE_AGENDA}
    )


# ---------- API ----------

MAX_FOTO_BYTES = 20 * 1024 * 1024


@app.post("/api/bericht")
async def bericht_in(
    request: Request,
    achtergrond: BackgroundTasks,
    tekst: str = Form(""),
    klant: str = Form("demo"),
    foto: UploadFile | None = File(None),
):
    jpeg, media_type, foto_url = None, "image/jpeg", None
    if foto is not None and foto.filename:
        data = await foto.read()
        if len(data) > MAX_FOTO_BYTES:
            raise HTTPException(413, "Foto is groter dan 20 MB.")
        try:
            jpeg, media_type, naam = fotos.verwerk(data, FOTO_MAP)
        except fotos.FotoFout as fout:
            raise HTTPException(422, str(fout)) from fout
        foto_url = f"/fotos/{naam}"
    if not tekst.strip() and jpeg is None:
        raise HTTPException(422, "Stuur tekst, een foto of allebei.")

    log = logboek(request)
    uitkomst = verwerk_bericht(log, klant, tekst, foto=jpeg, media_type=media_type, foto_url=foto_url)
    if uitkomst["route"] == "gewone_rij":
        # De AI draait op de achtergrond; de schermen zien het resultaat vanzelf verschijnen.
        achtergrond.add_task(
            ai_uitlezen, log, klant, tekst, jpeg, media_type, lees_uit, uitkomst["melding_id"], agenda(request)
        )
    return uitkomst


@app.get("/api/acties")
def acties(request: Request, na_id: int = 0):
    return logboek(request).lees(na_id=na_id)


@app.get("/api/rekensom")
def api_rekensom(
    oproepen_per_week: float = Query(ge=0),
    deel_gemist_pct: float = Query(ge=0, le=100),
    waarde_klus: float = Query(ge=0),
    deel_klus_pct: float = Query(rekensom.VOORBEELD["deel_klus_pct"], ge=0, le=100),
):
    try:
        return rekensom.bereken(oproepen_per_week, deel_gemist_pct, waarde_klus, deel_klus_pct)
    except ValueError as fout:
        raise HTTPException(422, str(fout)) from fout


@app.post("/api/voorstel/{voorstel_id}/{keuze}")
def voorstel_keuze(voorstel_id: int, keuze: str, request: Request):
    log, ag = logboek(request), agenda(request)
    try:
        if keuze == "goedkeuren":
            return planning.keur_goed(log, ag, voorstel_id)
        if keuze == "andere-tijd":
            return planning.andere_tijd(log, ag, voorstel_id)
        if keuze == "zelf-bellen":
            return planning.zelf_bellen(log, voorstel_id)
    except planning.PlanningFout as fout:
        raise HTTPException(409, str(fout)) from fout
    raise HTTPException(404, "Onbekende keuze.")


@app.get("/api/agenda")
def api_agenda(request: Request):
    dagen = werkdagen(date.today(), 5)
    return {
        "monteurs": MONTEURS,
        "dagen": [d.isoformat() for d in dagen],
        "afspraken": agenda(request).afspraken(dagen[0], (dagen[-1] - dagen[0]).days + 1),
    }


@app.post("/api/reset")
def reset(request: Request):
    logboek(request).reset()
    agenda(request).vul_demo_week()
    return {"status": "leeg"}


@app.get("/health")
def health():
    return {"status": "ok"}
