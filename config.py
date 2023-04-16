import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get("secret_key")

USERS_FILE = os.environ.get("users_path")
ACCOUNTS_FILE = os.environ.get("accounts_path")

DEFAULT_LAST_FETCHED = "01/01/1990"
DEFAULT_RANK = "Unknown"
DEFAULT_RR = "??"

MASTER_KEY = os.environ.get("master_key")
