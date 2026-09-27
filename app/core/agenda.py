"""US-4: demo-agenda met drie fictieve monteurs en een gevulde week.

De lokale agenda staat in dezelfde SQLite-database als het logboek. Zodra de
Google-agenda van OMNIA klaarstaat, komt daar een variant met dezelfde methodes bij.
"""

import random
import sqlite3
import threading
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path

MONTEURS = ["Jeroen Bakker", "Sanne de Wit", "Mehmet Yilmaz"]

# Werkblokken per dag.
BLOKKEN = [(time(8), time(10)), (time(10), time(12)), (time(13), time(15)), (time(15), time(17))]

# Gewone klussen om de week mee te vullen.
KLUSSEN = [
    "Onderhoud cv-ketel", "Onderhoud cv-ketel", "Storing Nefit EA", "Radiator vervangen",
    "Thermostaat ophangen", "Lekkage expansievat", "Onderhoud warmtepomp", "Ketel vervangen",
    "Storing Remeha", "Inspectie rookgasafvoer", "Vloerverwarming spoelen", "Onderhoud boiler",
]

VULGRAAD = 0.7  # deel van de blokken dat al bezet is

DAGEN = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
MAANDEN = ["januari", "februari", "maart", "april", "mei", "juni", "juli",
           "augustus", "september", "oktober", "november", "december"]


@dataclass(frozen=True)
class Blok:
    monteur: str
    start: datetime
    eind: datetime

    def als_dict(self) -> dict:
        return {"monteur": self.monteur, "start": self.start.isoformat(), "eind": self.eind.isoformat()}


def werkdagen(vanaf: date, aantal: int) -> list[date]:
    dagen, d = [], vanaf
    while len(dagen) < aantal:
        if d.weekday() < 5:
            dagen.append(d)
        d += timedelta(days=1)
    return dagen


def nette_tijd(start: datetime, eind: datetime) -> str:
    """'dinsdag 30 september, 10:00–12:00'"""
    return f"{DAGEN[start.weekday()]} {start.day} {MAANDEN[start.month - 1]}, {start:%H:%M}–{eind:%H:%M}"


class Agenda:
    def __init__(self, pad: Path | str):
        self.pad = str(pad)
        self._slot = threading.Lock()
        with self._verbind() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS afspraken (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    monteur TEXT NOT NULL,
                    start TEXT NOT NULL,
                    eind TEXT NOT NULL,
                    titel TEXT NOT NULL,
                    soort TEXT NOT NULL  -- 'bezet' (demo-vulling) of 'gepland' (via OMNIA)
                )"""
            )

    def _verbind(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.pad)
        db.row_factory = sqlite3.Row
        return db

    # ---------- Vullen ----------

    def vul_demo_week(self, vanaf: date | None = None, zaad: int = 7) -> None:
        """Wist de agenda en vult de komende vijf werkdagen voor ~70%. Altijd dezelfde week bij hetzelfde zaad."""
        vanaf = vanaf or date.today()
        kans = random.Random(zaad)
        rijen = []
        for dag in werkdagen(vanaf, 5):
            for monteur in MONTEURS:
                for van, tot in BLOKKEN:
                    if kans.random() < VULGRAAD:
                        rijen.append((monteur, datetime.combine(dag, van).isoformat(),
                                      datetime.combine(dag, tot).isoformat(), kans.choice(KLUSSEN), "bezet"))
        with self._slot, self._verbind() as db:
            db.execute("DELETE FROM afspraken")
            db.executemany("INSERT INTO afspraken (monteur, start, eind, titel, soort) VALUES (?, ?, ?, ?, ?)", rijen)

    def is_leeg(self) -> bool:
        with self._verbind() as db:
            return db.execute("SELECT COUNT(*) FROM afspraken").fetchone()[0] == 0

    # ---------- Lezen ----------

    def afspraken(self, vanaf: date, dagen: int = 7) -> list[dict]:
        tot = datetime.combine(vanaf + timedelta(days=dagen), time(0))
        with self._verbind() as db:
            rijen = db.execute(
                "SELECT * FROM afspraken WHERE start >= ? AND start < ? ORDER BY start, monteur",
                (datetime.combine(vanaf, time(0)).isoformat(), tot.isoformat()),
            ).fetchall()
        return [dict(r) for r in rijen]

    def _bezet(self) -> set[tuple[str, str]]:
        with self._verbind() as db:
            return {(r["monteur"], r["start"]) for r in db.execute("SELECT monteur, start FROM afspraken")}

    def vrije_blokken(self, na: datetime, aantal: int = 10, dagen_vooruit: int = 10) -> list[Blok]:
        """Vrije blokken die na het gegeven moment beginnen, vroegste eerst."""
        bezet = self._bezet()
        vrij: list[Blok] = []
        for dag in werkdagen(na.date(), dagen_vooruit):
            for van, tot in BLOKKEN:
                start = datetime.combine(dag, van)
                if start <= na:
                    continue
                for monteur in MONTEURS:
                    if (monteur, start.isoformat()) not in bezet:
                        vrij.append(Blok(monteur, start, datetime.combine(dag, tot)))
                        if len(vrij) >= aantal:
                            return vrij
        return vrij

    def is_vrij(self, blok: Blok) -> bool:
        return (blok.monteur, blok.start.isoformat()) not in self._bezet()

    # ---------- Schrijven ----------

    def plan(self, blok: Blok, titel: str) -> int:
        with self._slot, self._verbind() as db:
            if db.execute("SELECT 1 FROM afspraken WHERE monteur = ? AND start = ?",
                          (blok.monteur, blok.start.isoformat())).fetchone():
                raise ValueError("Dit blok is inmiddels bezet.")
            cur = db.execute(
                "INSERT INTO afspraken (monteur, start, eind, titel, soort) VALUES (?, ?, ?, ?, 'gepland')",
                (blok.monteur, blok.start.isoformat(), blok.eind.isoformat(), titel),
            )
            return cur.lastrowid
