"""Test de WhatsApp-koppeling: stuurt twee berichten naar WHATSAPP_TEST_ONTVANGER.

Gebruik:  .venv\Scripts\python -m scripts.test_whatsapp
"""

from app import config
from app.core import whatsapp


def main() -> None:
    print("1. Verbinding controleren...")
    info = whatsapp.controleer_verbinding()
    print(f"   OK: testnummer {info.get('display_phone_number')} ({info.get('verified_name')})")

    naar = config.WHATSAPP_TEST_ONTVANGER
    print(f"2. Sjabloon 'hello_world' sturen naar ...{naar[-4:]}")
    print(f"   OK: bericht-ID {whatsapp.stuur_sjabloon(naar, 'hello_world', taal='en_US')}")

    print("3. Vrij tekstbericht sturen (komt alleen aan als je < 24 uur geleden zelf iets naar het testnummer stuurde)")
    try:
        whatsapp.stuur_tekst(naar, f"Test vanuit OMNIA namens {config.BEDRIJFSNAAM}. De koppeling werkt!")
        print("   OK: verstuurd")
    except whatsapp.WhatsAppFout as fout:
        print(f"   Niet verstuurd: {fout}")


if __name__ == "__main__":
    main()
