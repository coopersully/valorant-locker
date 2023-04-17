from datetime import datetime, timedelta

import requests

from app import db
from config import DEFAULT_RANK, DEFAULT_RR, DEFAULT_LAST_UPDATED


class ValorantAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(50), nullable=False)
    display_tag = db.Column(db.String(10), nullable=False)
    region = db.Column(db.String(2), nullable=False)
    rank = db.Column(db.String(50), nullable=True)
    rr = db.Column(db.Integer, nullable=True)
    last_updated = db.Column(db.TIMESTAMP, nullable=True)

    def __init__(self, username, password, display_name, display_tag, region):
        self.username = username
        self.password = password
        self.display_name = display_name
        self.display_tag = display_tag
        self.region = region
        self.rank = DEFAULT_RANK
        self.rr = DEFAULT_RR
        self.last_updated: datetime = DEFAULT_LAST_UPDATED


def fetch_account_details(account):
    acc = f"{account.display_name}#{account.display_tag}"
    print(f"Fetching account details for {acc}...")

    now = datetime.now()
    if (now - account.last_updated) < timedelta(days=3):
        print(f"Already fetched recently; sending old data.")
        return account

    url = f"https://api.kyroskoh.xyz/valorant/v1/mmr/" \
          f"{account.region}/{account.display_name.replace(' ', '%20')}/" \
          f"{account.display_tag}"
    response = requests.get(url)

    if response.status_code == 200:
        rank_rr = response.text.split(" - ")
        if len(rank_rr) == 2:

            account.rank = rank_rr[0]
            if account.rank == 'null':
                account.rank = DEFAULT_RANK

            account.rr = rank_rr[1].removesuffix('RR.')
            if account.rr == 'null':
                account.rr = DEFAULT_RR

            account.last_updated = now
        else:
            print(f"Unexpected API response format: {response.text}")
    else:
        print(f"API request for {acc} failed with status code {response.status_code}.")
        print(f"Setting rank to '{DEFAULT_RANK}' and RR to '{DEFAULT_RR}'.")

        account.rank = DEFAULT_RANK
        account.rr = DEFAULT_RR

    print(f"Fetching account details for {acc}... Done!")
    db.session.add(account)
    db.session.commit()
    return account