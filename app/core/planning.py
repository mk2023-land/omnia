"""US-4: planningsvoorstel dat de planner met één tik goedkeurt.

Regels:
- Voorstel = het eerste vrije blok. Bij spoed vanaf nu, anders vanaf morgen.
- Drie keuzes: goedkeuren, andere tijd, zelf bellen.
- Zonder goedkeuring gaat er niets naar de klant.
"""

from datetime import datetime, time, timedelta

from app import config
from app.core import berichten
from app.core.agenda import Agenda, Blok, nette_tijd
from app.core.logboek import Logboek


class PlanningFout(Exception):
    pass


def _titel(u: dict) -> str:
    delen = [u.get("merk"), u.get("foutcode"), u.get("klacht")]
    return " · ".join(d for d in delen if d) or "Storing"


def maak_voorstel(
    logboek: Logboek, agenda: Agenda, klant: str, melding_id: int, uitlezing: dict,
    na: datetime | None = None, nu: datetime | None = None,
) -> dict:
    nu = nu or datetime.now()
    spoed = bool(uitlezing.get("spoed"))
    if na is None:
        na = nu if spoed else datetime.combine(nu.date() + timedelta(days=1), time(0))
        reden = "Spoed: eerste vrije blok vanaf nu" if spoed else "Geen spoed: eerste vrije blok vanaf morgen"
    else:
        reden = "Andere tijd: eerstvolgende vrije blok"

    vrij = agenda.vrije_blokken(na, aantal=1)
    if not vrij:
        return logboek.schrijf(klant, "geen_voorstel", melding_id=melding_id,
                               reden="Geen vrij blok in de komende twee weken. Bel de klant zelf.")
    blok = vrij[0]
    voorstel = logboek.schrijf(
        klant, "voorstel",
        melding_id=melding_id,
        **blok.als_dict(),
        tijd_tekst=nette_tijd(blok.start, blok.eind),
        reden=reden,
        titel=_titel(uitlezing),
        spoed=spoed,
    )
    berichten.meld_planner(
        logboek,
        f"Nieuw voorstel ({reden.lower()}):\n{voorstel['titel']}\n{voorstel['tijd_tekst']} · {blok.monteur}\n\n"
        "Antwoord 1 = goedkeuren, 2 = andere tijd, 3 = zelf bellen.",
    )
    return voorstel


AFHANDELING = {"goedkeuring", "andere_tijd", "zelf_bellen"}


def open_voorstel(logboek: Logboek) -> dict | None:
    """Het nieuwste voorstel dat nog niet is afgehandeld (voor de planner-telefoon)."""
    acties = logboek.lees()
    afgehandeld = {a.get("voorstel_id") for a in acties if a["soort"] in AFHANDELING}
    open_ = [a for a in acties if a["soort"] == "voorstel" and a["id"] not in afgehandeld]
    return open_[-1] if open_ else None


def _voorstel(logboek: Logboek, voorstel_id: int) -> dict:
    v = logboek.haal(voorstel_id)
    if not v or v["soort"] != "voorstel":
        raise PlanningFout("Dit voorstel bestaat niet.")
    afgehandeld = [a for a in logboek.lees(na_id=voorstel_id)
                   if a.get("voorstel_id") == voorstel_id and a["soort"] in AFHANDELING]
    if afgehandeld:
        raise PlanningFout("Dit voorstel is al afgehandeld.")
    return v


def keur_goed(logboek: Logboek, agenda: Agenda, voorstel_id: int) -> dict:
    v = _voorstel(logboek, voorstel_id)
    blok = Blok(v["monteur"], datetime.fromisoformat(v["start"]), datetime.fromisoformat(v["eind"]))
    try:
        afspraak_id = agenda.plan(blok, v["titel"])
    except ValueError as fout:
        raise PlanningFout(f"{fout} Kies een andere tijd.") from fout

    tekst = (
        f"Goed nieuws! Uw afspraak staat:\n{v['tijd_tekst']}\n"
        f"Monteur {v['monteur']} komt bij u langs.\n\nMet vriendelijke groet,\n{config.BEDRIJFSNAAM}"
    )
    berichten.verstuur(logboek, v["klant"], tekst)
    return logboek.schrijf(v["klant"], "goedkeuring", voorstel_id=voorstel_id, afspraak_id=afspraak_id,
                           monteur=v["monteur"], tijd_tekst=v["tijd_tekst"])


def andere_tijd(logboek: Logboek, agenda: Agenda, voorstel_id: int) -> dict:
    v = _voorstel(logboek, voorstel_id)
    logboek.schrijf(v["klant"], "andere_tijd", voorstel_id=voorstel_id)
    return maak_voorstel(logboek, agenda, v["klant"], v["melding_id"], {"spoed": v["spoed"], "klacht": v["titel"]},
                         na=datetime.fromisoformat(v["start"]))


def zelf_bellen(logboek: Logboek, voorstel_id: int) -> dict:
    v = _voorstel(logboek, voorstel_id)
    return logboek.schrijf(v["klant"], "zelf_bellen", voorstel_id=voorstel_id)
