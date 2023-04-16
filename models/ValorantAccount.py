import json
from datetime import datetime, timedelta

import requests

from config import DEFAULT_RANK, DEFAULT_RR, DEFAULT_LAST_FETCHED


class ValorantAccount:
    def __init__(self, username, password, display_name, display_tag, region, rank=None, rr=None, last_fetched=None):
        self.username = username
        self.password = password
        self.display_name = display_name
        self.display_tag = display_tag
        self.region = region
        self.rank = rank or DEFAULT_RANK
        self.rr = rr or DEFAULT_RR
        self.last_fetched = last_fetched or DEFAULT_LAST_FETCHED


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


# Fetch account details and update the account object
def fetch_account_details(account):
    acc = f"{account['display']['name']}#{account['display']['tag']}"
    print(f"Fetching account details for {acc}...")

    account.setdefault('rank', DEFAULT_RANK)
    account.setdefault('rr', DEFAULT_RR)
    last_fetched = account.get("last_fetched", DEFAULT_LAST_FETCHED)
    now = datetime.now()

    if last_fetched:
        last_fetched_dt = datetime.strptime(last_fetched, "%m/%d/%Y")
        if (now - last_fetched_dt) < timedelta(days=3):
            print(f"Already fetched recently; sending old data.")
            return account

    url = f"https://api.kyroskoh.xyz/valorant/v1/mmr/" \
          f"{account['region']}/{account['display']['name'].replace(' ', '%20')}/" \
          f"{account['display']['tag']}"
    response = requests.get(url)

    if response.status_code == 200:
        rank_rr = response.text.split(" - ")
        if len(rank_rr) == 2:

            account['rank'] = rank_rr[0]
            if account['rank'] == 'null':
                account['rank'] = DEFAULT_RANK

            account['rr'] = rank_rr[1].removesuffix('RR.')
            if account['rr'] == 'null':
                account['rr'] = DEFAULT_RR

            account['last_fetched'] = now.strftime("%m/%d/%Y")
        else:
            print(f"Unexpected API response format: {response.text}")
    else:
        print(f"API request for {acc} failed with status code {response.status_code}.")
        print(f"Setting rank to '{DEFAULT_RANK}' and RR to '{DEFAULT_RR}'.")

        account['rank'] = DEFAULT_RANK
        account['rr'] = DEFAULT_RR

    print(f"Fetching account details for {acc}... Done!")
    return account
