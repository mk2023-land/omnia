"""OMNIA-demo: webserver voor de landingspagina en de demo's per user story.

Starten:  .venv\\Scripts\\python -m uvicorn app.main:app --reload
"""

from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app import config
from app.core import fotos, rekensom
from app.core.logboek import Logboek
from app.core.uitlezen import lees_uit
from app.core.werkstroom import ai_uitlezen, verwerk_bericht
from app.stories import BOUWVOLGORDE, STORIES

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


@app.get("/demo/telefoon", response_class=HTMLResponse)
@app.get("/demo/gas", response_class=HTMLResponse)
def demotelefoon(request: Request):
    return templates.TemplateResponse(
        request, "telefoon.html", {"bedrijfsnaam": config.BEDRIJFSNAAM, "met_telefoon": True}
    )


@app.get("/planner", response_class=HTMLResponse)
def planner(request: Request):
    return templates.TemplateResponse(
        request, "telefoon.html", {"bedrijfsnaam": config.BEDRIJFSNAAM, "met_telefoon": False}
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
        achtergrond.add_task(ai_uitlezen, log, klant, tekst, jpeg, media_type, lees_uit)
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


@app.post("/api/reset")
def reset(request: Request):
    logboek(request).reset()
    return {"status": "leeg"}


@app.get("/health")
def health():
    return {"status": "ok"}
