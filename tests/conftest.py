import os
import tempfile

# Tests schrijven nooit in de echte demo-database, sturen nooit echte WhatsApp-berichten
# en roepen nooit de echte AI aan (die kost geld).
os.environ["DB_PAD"] = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["SIMULATIE_WHATSAPP"] = "true"
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["SIMULATIE_TELEFONIE"] = "true"
os.environ["TESTONTVANGERS"] = "+31600000000"
os.environ["TWILIO_AUTH_TOKEN"] = "testtoken"
os.environ["PUBLIEK_ADRES"] = "https://omnia.test"
