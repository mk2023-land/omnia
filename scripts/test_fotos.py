"""Test US-3 op eigen foto's in testfotos/ (zie testfotos/README.md).

Gebruik:  .venv\Scripts\python -m scripts.test_fotos
"""

import csv
import time
from pathlib import Path

from app.core.uitlezen import UitleesFout, lees_uit

MAP = Path(__file__).resolve().parent.parent / "testfotos"
VELDEN = ("merk", "type", "foutcode")
MEDIA = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}


def gelijk(verwacht: str, gelezen: str | None) -> bool:
    norm = lambda s: "".join((s or "").lower().split()).replace(".", "")  # noqa: E731
    return norm(verwacht) == norm(gelezen)


def main() -> None:
    fotos = sorted(p for p in MAP.iterdir() if p.suffix.lower() in MEDIA)
    if not fotos:
        print(f"Geen foto's gevonden in {MAP}")
        return

    verwacht: dict[str, dict] = {}
    csv_pad = MAP / "verwacht.csv"
    if csv_pad.exists():
        with csv_pad.open(encoding="utf-8-sig") as f:
            verwacht = {r["bestand"]: r for r in csv.DictReader(f, delimiter=";")}

    goed = totaal = gegokt = 0
    for foto in fotos:
        start = time.time()
        try:
            u = lees_uit("", foto.read_bytes(), MEDIA[foto.suffix.lower()])
        except UitleesFout as fout:
            print(f"{foto.name:30} FOUT: {fout}")
            continue
        regel = " | ".join(f"{v}: {u[v] or '–'}" for v in VELDEN)
        print(f"{foto.name:30} {time.time() - start:4.1f}s  {regel}")

        if foto.name in verwacht:
            for v in VELDEN:
                e = (verwacht[foto.name].get(v) or "").strip()
                totaal += 1
                if gelijk(e, u[v]):
                    goed += 1
                else:
                    if not e and u[v]:
                        gegokt += 1  # AI vulde iets in dat er niet staat: het ergste soort fout
                    print(f"{'':30}   ✗ {v}: verwacht '{e or '(leeg)'}', gelezen '{u[v] or '(leeg)'}'")

    if totaal:
        print(f"\nScore: {goed}/{totaal} velden goed ({goed / totaal:.0%}), waarvan {gegokt} keer gegokt.")


if __name__ == "__main__":
    main()
