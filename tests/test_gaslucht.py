"""Tests voor US-2 met echte formuleringen, ook met tikfouten."""

import pytest

from app.core.veiligheid import NOODNUMMER_GAS, controleer_gaslucht, veiligheidsbericht

MOET_ALARM = [
    # Rechttoe rechtaan
    "ik ruik gas",
    "Ik ruik gas!!",
    "gaslucht in de keuken",
    "Er hangt een gaslucht in huis",
    "het ruikt naar gas bij de ketel",
    "Het stinkt hier naar gas",
    "volgens mij hebben we een gaslek",
    "Gas lekt bij de meter denk ik",
    "sterke gasgeur in de meterkast",
    "gas",
    "GAS!!!",
    "help gas",
    "mijn buurvrouw zegt dat ze gas rook in het trappenhuis",
    "ik heb gas geroken toen ik thuiskwam",
    "gasfornuis ruikt raar",
    "de gasketel stinkt",
    "Er is een gaslekkage denk ik",
    # Tikfouten
    "ik riuk gas",
    "ik ruik gass",
    "gasluht in de gang",
    "gaslucth bij de cv",
    "gaslugt",
    "ik ruik gaaas",
    "ikruikgas",
    "gasgeuer in huis",
    # Accenten en hoofdletters
    "GÁSLUCHT",
    # Engels
    "I smell gas",
    "gas leak in the kitchen",
    # Liever te vaak dan te weinig
    "ik ruik geen gas meer, maar net wel",
]

GEEN_ALARM = [
    "mijn cv-ketel doet het niet",
    "Remeha ketel geeft foutcode F28",
    "geen warm water sinds vanochtend",
    "de gasketel geeft storing E133",
    "gasrekening klopt niet",
    "de gasmeter moet vervangen worden",
    "de radiatoren worden niet warm",
    "druk van de ketel staat op 0,5 bar",
    "er komt rook uit de schoorsteen",
    "de ketel maakt een raar geluid",
    "",
]


@pytest.mark.parametrize("tekst", MOET_ALARM)
def test_gaslucht_wordt_herkend(tekst):
    assert controleer_gaslucht(tekst) is not None, tekst


@pytest.mark.parametrize("tekst", GEEN_ALARM)
def test_gewone_storing_geeft_geen_alarm(tekst):
    assert controleer_gaslucht(tekst) is None, tekst


def test_veiligheidsbericht_bevat_noodnummer_en_bedrijfsnaam():
    bericht = veiligheidsbericht("Installatiebedrijf Test")
    assert NOODNUMMER_GAS in bericht
    assert "112" in bericht
    assert "Installatiebedrijf Test" in bericht
