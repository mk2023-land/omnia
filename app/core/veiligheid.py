"""US-2: gaslucht gaat altijd voor.

Vaste regel, geen taalmodel. Deze controle draait vóór elke AI-stap en werkt dus
ook als de AI-dienst niet bereikbaar is.

Uitgangspunt: liever één keer te vaak alarm dan één keer te weinig. Daarom telt
ook "ik ruik geen gas meer" als treffer; de planner beoordeelt dat zelf.
"""

import re
import unicodedata
from dataclasses import dataclass

NOODNUMMER_GAS = "0800-9009"

# Woorden die op zichzelf al gaslucht of een gaslek betekenen.
GASWOORDEN = {
    "gaslucht", "gasgeur", "gaslek", "gaslekkage", "gasstank", "gaslucjt",
    "gaslekt", "gaslekken", "gasluchtje", "ruikgas", "gassmell", "gasleak",
}

# Losse woorden voor gas (inclusief veelvoorkomende tikfouten).
GAS = {"gas", "gass", "gaz", "gsa", "gaas"}

# Woorden die op ruiken of lekken wijzen. In combinatie met gas: treffer.
SIGNAALWOORDEN = {
    "ruik", "ruiken", "ruikt", "rook", "roken", "geroken", "stinkt", "stinken",
    "stank", "lucht", "luchtje", "geur", "lek", "lekt", "lekken", "lekkage",
    "ontsnapt", "sist", "sissen", "smell", "smells", "leak", "leaking",
}

# Hoeveel woorden gas en het signaalwoord uit elkaar mogen staan.
VENSTER = 4


@dataclass(frozen=True)
class Treffer:
    reden: str
    woorden: tuple[str, ...]


def normaliseer(tekst: str) -> list[str]:
    """Kleine letters, geen accenten, geen leestekens, herhaalde letters ingekort."""
    tekst = unicodedata.normalize("NFKD", tekst.lower())
    tekst = "".join(t for t in tekst if not unicodedata.combining(t))
    tekst = re.sub(r"[^a-z0-9]+", " ", tekst)
    tekst = re.sub(r"(.)\1{2,}", r"\1\1", tekst)  # "gassss" -> "gass"
    return tekst.split()


def _afstand(a: str, b: str) -> int:
    """Aantal tikfouten tussen a en b. Twee verwisselde letters tellen als één fout."""
    if abs(len(a) - len(b)) > 2:
        return 3
    d = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        d[i][0] = i
    for j in range(len(b) + 1):
        d[0][j] = j
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            kosten = a[i - 1] != b[j - 1]
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + kosten)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[-1][-1]


def _lijkt_op(woord: str, lijst: set[str]) -> bool:
    if woord in lijst:
        return True
    # Tikfouten alleen toestaan bij langere woorden, anders te veel valse treffers.
    if len(woord) < 4:
        return False
    marge = 2 if len(woord) >= 7 else 1
    return any(len(w) >= 4 and _afstand(woord, w) <= marge for w in lijst)


def _is_gas(woord: str) -> bool:
    return woord in GAS


def _is_gas_samenstelling(woord: str) -> bool:
    """gasketel, gasfornuis, gasmeter: gas-woorden die op zichzelf geen alarm zijn."""
    return woord.startswith("gas") and len(woord) > 4


def controleer_gaslucht(tekst: str) -> Treffer | None:
    """Geeft een Treffer terug als het bericht op gaslucht of een gaslek wijst."""
    woorden = normaliseer(tekst)
    if not woorden:
        return None

    # 1. Een woord dat zelf al gaslucht betekent (ook met tikfout).
    for w in woorden:
        if _lijkt_op(w, GASWOORDEN):
            return Treffer("gaswoord", (w,))

    # 2. Een bericht dat alleen uit "gas" bestaat, of bijna: "gas!!", "help gas".
    if len(woorden) <= 2 and any(_is_gas(w) for w in woorden):
        return Treffer("alleen gas", tuple(woorden))

    # 3. Gas (of gasketel, gasfornuis...) met een signaalwoord in de buurt.
    for i, w in enumerate(woorden):
        if not (_is_gas(w) or _is_gas_samenstelling(w)):
            continue
        buren = woorden[max(0, i - VENSTER): i + VENSTER + 1]
        for b in buren:
            if b != w and _lijkt_op(b, SIGNAALWOORDEN):
                return Treffer("gas + signaalwoord", (w, b))

    # 4. Aan elkaar geschreven zonder spaties: "ikruikgas".
    aaneen = "".join(woorden)
    for w in GASWOORDEN:
        if w in aaneen:
            return Treffer("gaswoord", (w,))

    return None


def veiligheidsbericht(bedrijfsnaam: str) -> str:
    """Het bericht dat de klant direct krijgt bij een treffer."""
    return (
        f"Ruikt u gas? Bel direct {NOODNUMMER_GAS} (gratis, dag en nacht bereikbaar).\n\n"
        "Doe nu het volgende:\n"
        "• Geen vuur, niet roken, geen lichtknoppen of stekkers gebruiken\n"
        "• Zet ramen en deuren open\n"
        "• Draai de gaskraan bij de meter dicht als dat veilig kan\n"
        "• Ga naar buiten en bel vanaf buiten\n\n"
        "Bij direct gevaar: bel 112.\n\n"
        f"{bedrijfsnaam} is op de hoogte en neemt contact met u op."
    )
