"""OMNIA-demo: webserver voor de landingspagina en de demo's per user story.

Starten:  .venv\\Scripts\\python -m uvicorn app.main:app --reload
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app import config
from app.core.logboek import Logboek
from app.core.werkstroom import verwerk_bericht
from app.stories import BOUWVOLGORDE, STORIES

APP_DIR = Path(__file__).resolve().parent

app = FastAPI(title="OMNIA-demo")
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")
templates = Jinja2Templates(directory=APP_DIR / "templates")
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


@app.post("/api/reset")
def reset(request: Request):
    logboek(request).reset()
    return {"status": "leeg"}


@app.get("/health")
def health():
    return {"status": "ok"}
