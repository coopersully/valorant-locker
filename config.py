import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get("secret_key")

DEFAULT_RANK = "Unknown"
DEFAULT_RR = "??"
DEFAULT_LAST_UPDATED = datetime.strptime("01/01/1990", "%m/%d/%Y")

MASTER_KEY = os.environ.get("master_key")
DATABASE_PATH = os.environ.get("database_path")