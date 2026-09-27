"""Voorbeeldberichten voor de demotelefoon, per user story.

Elke knop stuurt een bericht als klant. `foto` verwijst naar een bestand in
app/static/img/voorbeelden/ (nagemaakte foto's). Voeg hier gerust voorbeelden toe.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Voorbeeld:
    label: str
    tekst: str = ""
    foto: str | None = None


@dataclass(frozen=True)
class Groep:
    titel: str
    uitleg: str
    voorbeelden: tuple[Voorbeeld, ...]
    soort: str = ""  # "alarm" kleurt de knoppen rood


GROEPEN = [
    Groep(
        "Gaslucht", "US-2 · gaat altijd voor, ook met tikfouten",
        (
            Voorbeeld("Ik ruik gas", "ik ruik gas"),
            Voorbeeld("Gaslucht in de keuken", "Er hangt een gaslucht in de keuken"),
            Voorbeeld("Tikfout: ik riuk gass", "ik riuk gass"),
            Voorbeeld("Het stinkt naar gas", "het stinkt hier naar gas bij de meterkast"),
            Voorbeeld("Alleen: GAS!!", "GAS!!"),
        ),
        soort="alarm",
    ),
    Groep(
        "Geen gasalarm", "US-2 · gas-woorden die géén alarm moeten geven",
        (
            Voorbeeld("Gasketel in storing", "mijn gasketel staat in storing"),
            Voorbeeld("Vraag over gasrekening", "klopt mijn gasrekening wel? de ketel verbruikt veel"),
        ),
    ),
    Groep(
        "Storing in tekst", "US-3 en US-4 · uitlezen en planningsvoorstel",
        (
            Voorbeeld("Remeha F28, geen warm water", "Remeha ketel geeft F28, geen warm water"),
            Voorbeeld("Intergas F4, verwarming doet niks", "Mijn Intergas geeft F4 en de verwarming doet niks"),
            Voorbeeld("Nefit EA op display", "Onze Nefit ketel geeft EA op het display"),
            Voorbeeld("Vaillant F.22, druk te laag", "Vaillant ketel zegt F.22, de druk staat onder de 1 bar"),
            Voorbeeld("Tikkend geluid (geen spoed)", "mijn ketel maakt sinds gisteren een tikkend geluid"),
            Voorbeeld("Onderhoud (geen spoed)", "Graag een onderhoudsbeurt voor de cv-ketel, geen haast"),
            Voorbeeld("Vaag: hij doet het niet", "hij doet het niet"),
        ),
    ),
    Groep(
        "Met foto", "US-3 · nagemaakte foto's van typeplaatje en display",
        (
            Voorbeeld("Display met F28", "Dit staat er op het schermpje, geen warm water", "display-f28.jpg"),
            Voorbeeld("Typeplaatje Remeha", "Hier is het typeplaatje, verwarming blijft koud", "remeha.jpg"),
            Voorbeeld("Typeplaatje Intergas + F4", "Hij geeft F4 op het schermpje", "intergas.jpg"),
            Voorbeeld("Typeplaatje Nefit (alleen foto)", "", "nefit.jpg"),
            Voorbeeld("Typeplaatje Vaillant + lekkage", "Ketel lekt water aan de onderkant", "vaillant.jpg"),
            Voorbeeld("Onscherpe foto (niet gokken)", "typeplaatje", "onscherp.jpg"),
        ),
    ),
]
