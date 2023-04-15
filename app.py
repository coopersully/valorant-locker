import json
import os
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, login_required, login_user, logout_user, current_user

from User import load_users

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("secret_key")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

users = load_users()

DEFAULT_LAST_FETCHED = "01/01/1990"
DEFAULT_RANK = "Unknown"
DEFAULT_RR = "??"


# Load accounts from the JSON file
def load_accounts():
    try:
        with open('accounts.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


# Save accounts to the JSON file
def save_accounts(new_accounts_data):
    with open('accounts.json', 'w') as f:
        json.dump(new_accounts_data, f, indent=2)


accounts_data = load_accounts()


# Check user authentication before each request
@app.before_request
def check_authentication():
    # Exclude static folder from the authentication check
    if request.path.__contains__('.svg') or request.path.__contains__('.png') or request.path.__contains__(
            '.jpg') or request.path.__contains__('.css'):
        return

    if not current_user.is_authenticated and request.endpoint != 'login':
        print(f'Redirected request from {request.path}')
        return redirect(url_for('login'))


# Favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


# Display accounts and update them if necessary
@app.route('/')
@login_required
def accounts():
    accounts_updated = False

    for i, account in enumerate(accounts_data):
        last_fetched = account.get("last_fetched", DEFAULT_LAST_FETCHED)
        if last_fetched:
            last_fetched_dt = datetime.strptime(last_fetched, "%m/%d/%Y")
            if (datetime.now() - last_fetched_dt) >= timedelta(days=3):
                updated_account = fetch_account_details(account)
                accounts_data[i] = updated_account
                accounts_updated = True
        else:
            updated_account = fetch_account_details(account)
            accounts_data[i] = updated_account
            accounts_updated = True

    if accounts_updated:
        save_accounts(accounts_data)

    return render_template('accounts.html', accounts=accounts_data)


# Show the form to add a new account
@app.route('/add_account', methods=['GET'])
@login_required
def account_form():
    return render_template('account_form.html')


# Add a new account and save it
@app.route('/add_account', methods=['POST'])
@login_required
def add_account():
    new_account = {
        "username": request.form['username'],
        "password": request.form['password'],
        "display": {
            "name": request.form['display_name'],
            "tag": request.form['display_tag']
        },
        "region": request.form['region'],
        "rank": DEFAULT_RANK,
        "rr": DEFAULT_RR,
        "last_fetched": DEFAULT_LAST_FETCHED
    }
    accounts_data.append(new_account)
    save_accounts(accounts_data)
    return redirect(url_for('accounts'))


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

    url = f"https://api.kyroskoh.xyz/valorant/v1/mmr/{account['region']}/{account['display']['name'].replace(' ', '%20')}/{account['display']['tag']}"
    response = requests.get(url)

    if response.status_code == 200:
        rank_rr = response.text.split(" - ")
        if len(rank_rr) == 2:

            account['rank'] = rank_rr[0]
            if account['rank'] == 'null': account['rank'] = 'Unknown'

            account['rr'] = rank_rr[1].removesuffix('RR.')
            if account['rr'] == 'null': account['rr'] = '??'

            account['last_fetched'] = now.strftime("%m/%d/%Y")
        else:
            print(f"Unexpected API response format: {response.text}")
    else:
        print(f"API request for {acc} failed with status code {response.status_code}.")
        print(f"Setting rank to 'Unknown' and RR to '??'.")

        account['rank'] = 'Unknown'
        account['rr'] = '??'

    print(f"Fetching account details for {acc}... Done!")
    return account


@login_manager.user_loader
def load_user(auth_key):
    return users.get(auth_key)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        auth_key = request.form['auth_key']
        user = users.get(auth_key)
        if user:
            login_user(user)
            return redirect(url_for('accounts'))
        else:
            flash('Invalid authentication key.', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
