"""Actielog van OMNIA-core in een SQLite-database.

Elke stap in de werkstroom schrijft hier een regel. Het plannerscherm en later
het demoscherm (US-5) lezen alles hieruit.
"""

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path


class Logboek:
    def __init__(self, pad: Path | str):
        self.pad = str(pad)
        self._slot = threading.Lock()
        with self._verbind() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS acties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tijd TEXT NOT NULL,
                    klant TEXT NOT NULL,
                    soort TEXT NOT NULL,
                    data TEXT NOT NULL
                )"""
            )

    def _verbind(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.pad)
        db.row_factory = sqlite3.Row
        return db

    def schrijf(self, klant: str, soort: str, **data) -> dict:
        tijd = datetime.now().isoformat(timespec="milliseconds")
        with self._slot, self._verbind() as db:
            cur = db.execute(
                "INSERT INTO acties (tijd, klant, soort, data) VALUES (?, ?, ?, ?)",
                (tijd, klant, soort, json.dumps(data, ensure_ascii=False)),
            )
            return {"id": cur.lastrowid, "tijd": tijd, "klant": klant, "soort": soort, **data}

    def lees(self, soort: str | None = None, na_id: int = 0) -> list[dict]:
        sql = "SELECT * FROM acties WHERE id > ?"
        args: list = [na_id]
        if soort:
            sql += " AND soort = ?"
            args.append(soort)
        with self._verbind() as db:
            rijen = db.execute(sql + " ORDER BY id", args).fetchall()
        return [
            {"id": r["id"], "tijd": r["tijd"], "klant": r["klant"], "soort": r["soort"], **json.loads(r["data"])}
            for r in rijen
        ]

    def haal(self, actie_id: int) -> dict | None:
        with self._verbind() as db:
            r = db.execute("SELECT * FROM acties WHERE id = ?", (actie_id,)).fetchone()
        if r is None:
            return None
        return {"id": r["id"], "tijd": r["tijd"], "klant": r["klant"], "soort": r["soort"], **json.loads(r["data"])}

    def reset(self) -> None:
        with self._slot, self._verbind() as db:
            db.execute("DELETE FROM acties")
