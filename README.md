# OMNIA

Automatisering voor klus- en installatiebedrijven: van gemist telefoontje tot ingeplande monteur.
Deze repo bevat de interne demo: een landingspagina met alle user stories en per story een werkende demo.

## Starten (Windows)

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
.venv\Scripts\python -m uvicorn app.main:app --reload
```

Open daarna http://localhost:8000.

## Testen

```powershell
.venv\Scripts\python -m pytest
```

## Structuur

| Pad | Wat |
|---|---|
| `app/main.py` | Webserver (FastAPI) |
| `app/config.py` | Alle instellingen, gelezen uit `.env` |
| `app/stories.py` | De user stories en hun status op de landingspagina |
| `app/templates/` | HTML-pagina's |
| `app/static/` | Huisstijl (`css/omnia.css`) en logo |
| `tests/` | Tests |

## Simulatie

Elke externe dienst (Twilio, WhatsApp, Google Agenda) heeft een schakelaar in `.env`.
Staat die op `true`, dan wordt de dienst nagebootst en werkt de demo zonder account of internet.

## Bouwvolgorde

1. Landingspagina ✅
2. US-2 Gaslucht gaat altijd voor ✅ (`/demo/gas`, plannerscherm los op `/planner`)
3. US-5 Demoscherm met logboek en rekensom
4. US-3 Storing uitlezen uit foto en tekst
5. US-4 Planningsvoorstel in een demo-agenda
6. US-1 Demonummer belt terug
