"""Overzicht van de user stories zoals ze op de landingspagina staan.

Pas hier de status aan zodra een story verder is. De landingspagina leest deze lijst.
"""

from dataclasses import dataclass

# Mogelijke statussen, van begin tot eind.
STATUSSEN = {
    "gepland": "Gepland",
    "bezig": "Bezig",
    "gesimuleerd": "Werkt (gesimuleerd)",
    "live": "Werkt (echt)",
}


@dataclass(frozen=True)
class Story:
    code: str
    titel: str
    stap: str
    uitleg: str
    punten: tuple[str, ...]
    status: str = "gepland"
    demo_url: str | None = None

    @property
    def status_label(self) -> str:
        return STATUSSEN[self.status]


# Volgorde = volgorde in de keten, zoals de klant hem doorloopt.
STORIES: list[Story] = [
    Story(
        code="US-1",
        titel="Demonummer belt terug",
        stap="Gemiste oproep",
        uitleg="Niemand neemt op. Binnen een minuut krijgt de klant een WhatsApp of sms.",
        punten=(
            "Bericht binnen 60 seconden",
            "Vraagt merk, type, foutcode en foto van het typeplaatje",
            "Bedrijfsnaam aan te passen in één instelling",
        ),
        status="gesimuleerd",
        demo_url="/demo/telefoon",
    ),
    Story(
        code="US-2",
        titel="Gaslucht gaat altijd voor",
        stap="Veiligheid",
        uitleg="Een melding van gaslucht komt nooit in de gewone rij terecht.",
        punten=(
            "Vaste woordenlijst, gecontroleerd vóór elke AI-stap",
            "Direct 0800-9009 en een veiligheidstekst",
            "Werkt ook als de AI niet bereikbaar is",
        ),
        status="gesimuleerd",
        demo_url="/demo/telefoon",
    ),
    Story(
        code="US-3",
        titel="Storing uitlezen uit foto en tekst",
        stap="Uitlezen",
        uitleg="Uit een foto en een paar zinnen komt een nette samenvatting van de storing.",
        punten=(
            "Merk, type, foutcode, klacht en spoed",
            "Niet leesbaar blijft leeg: er wordt niets gegokt",
            "Spoed is een voorstel, met reden",
        ),
        status="live",
        demo_url="/demo/telefoon",
    ),
    Story(
        code="US-4",
        titel="Planningsvoorstel in een demo-agenda",
        stap="Plannen",
        uitleg="Een voorstel voor tijd en monteur dat de planner met één tik goedkeurt.",
        punten=(
            "Drie monteurs en een gevulde week",
            "Goedkeuren, andere tijd of zelf bellen",
            "Zonder goedkeuring gaat er niets naar de klant",
        ),
        status="gesimuleerd",
        demo_url="/demo/telefoon",
    ),
    Story(
        code="US-5",
        titel="Demoscherm met logboek en rekensom",
        stap="Resultaat",
        uitleg="Elke stap live op één scherm, plus wat gemiste oproepen per maand kosten.",
        punten=(
            "Logboek met tijden per stap",
            "Eigen cijfers invullen, aannames erbij",
            "Resetknop na elke run",
        ),
        status="gesimuleerd",
        demo_url="/demo",
    ),
]

# Bouwvolgorde (van makkelijk naar moeilijk), voor de voortgangsbalk.
BOUWVOLGORDE = ["US-2", "US-5", "US-3", "US-4", "US-1"]
