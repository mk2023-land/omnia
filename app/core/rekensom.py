"""US-5: wat gemiste oproepen een bedrijf per maand kosten.

Alle aannames komen mee in de uitkomst, zodat het demoscherm ze kan tonen.
"""

WEKEN_PER_MAAND = 52 / 12

# Voorbeeldcijfers. Op het scherm staan ze gemarkeerd als voorbeeld.
VOORBEELD = {
    "oproepen_per_week": 60,
    "deel_gemist_pct": 25,
    "waarde_klus": 250,
    "deel_klus_pct": 50,
}


def bereken(
    oproepen_per_week: float,
    deel_gemist_pct: float,
    waarde_klus: float,
    deel_klus_pct: float = VOORBEELD["deel_klus_pct"],
) -> dict:
    if min(oproepen_per_week, deel_gemist_pct, waarde_klus, deel_klus_pct) < 0:
        raise ValueError("Cijfers kunnen niet negatief zijn.")
    if deel_gemist_pct > 100 or deel_klus_pct > 100:
        raise ValueError("Een percentage kan niet boven 100 liggen.")

    oproepen_per_maand = oproepen_per_week * WEKEN_PER_MAAND
    gemist_per_maand = oproepen_per_maand * deel_gemist_pct / 100
    klussen_per_maand = gemist_per_maand * deel_klus_pct / 100
    omzet_per_maand = klussen_per_maand * waarde_klus

    return {
        "oproepen_per_maand": round(oproepen_per_maand, 1),
        "gemist_per_maand": round(gemist_per_maand, 1),
        "klussen_per_maand": round(klussen_per_maand, 1),
        "omzet_per_maand": round(omzet_per_maand),
        "omzet_per_jaar": round(omzet_per_maand * 12),
        "aannames": [
            f"Een maand telt {WEKEN_PER_MAAND:.2f} weken (52 weken / 12 maanden).".replace(".", ",", 1),
            f"Van de gemiste bellers zou {deel_klus_pct:g}% een klus zijn geworden.",
            "Een gemiste beller die niet terugbelt, gaat naar een ander bedrijf.",
            "Gerekend met omzet per klus, niet met winst.",
        ],
    }
