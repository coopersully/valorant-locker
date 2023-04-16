# Load accounts from the JSON file
import json


def load_accounts(accounts_file):
    try:
        with open(accounts_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        default = "[]"
        save_accounts(accounts_file, json.loads(default))
        return load_accounts(accounts_file)
    except json.JSONDecodeError:
        return []


# Save accounts to the JSON file
def save_accounts(accounts_file, accounts_json):
    with open(accounts_file, 'w') as f:
        json.dump(accounts_json, f, indent=2)
