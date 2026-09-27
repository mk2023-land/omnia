"""OMNIA-demo: webserver voor de landingspagina en de demo's per user story.

Starten:  .venv\\Scripts\\python -m uvicorn app.main:app --reload
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app import config
from app.core import rekensom
from app.core.logboek import Logboek
from app.core.werkstroom import verwerk_bericht
from app.stories import BOUWVOLGORDE, STORIES

APP_DIR = Path(__file__).resolve().parent

app = FastAPI(title="OMNIA-demo")
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")
templates = Jinja2Templates(directory=APP_DIR / "templates")
# Versienummer achter het stijlbestand, zodat de browser nooit een oude versie gebruikt.
templates.env.globals["css_versie"] = int((APP_DIR / "static/css/omnia.css").stat().st_mtime)
app.state.logboek = Logboek(config.DB_PAD)


def logboek(request: Request) -> Logboek:
    return request.app.state.logboek


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


@app.get("/demo/gas", response_class=HTMLResponse)
def demo_gas(request: Request):
    return templates.TemplateResponse(
        request, "demo_gas.html", {"bedrijfsnaam": config.BEDRIJFSNAAM, "met_telefoon": True}
    )


@app.get("/planner", response_class=HTMLResponse)
def planner(request: Request):
    return templates.TemplateResponse(
        request, "demo_gas.html", {"bedrijfsnaam": config.BEDRIJFSNAAM, "met_telefoon": False}
    )


# ---------- API ----------

class Bericht(BaseModel):
    klant: str = "demo"
    tekst: str


@app.post("/api/bericht")
def bericht_in(bericht: Bericht, request: Request):
    return verwerk_bericht(logboek(request), bericht.klant, bericht.tekst)


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


@app.post("/api/reset")
def reset(request: Request):
    logboek(request).reset()
    return {"status": "leeg"}


@app.get("/health")
def health():
    return {"status": "ok"}
