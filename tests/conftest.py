import os
import tempfile

# Tests schrijven nooit in de echte demo-database.
os.environ["DB_PAD"] = os.path.join(tempfile.mkdtemp(), "test.db")
