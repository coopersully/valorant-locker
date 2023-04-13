import json
from datetime import datetime, timedelta

import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_required, login_user, logout_user, current_user

from User import load_users

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Replace with your actual secret key

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

users = load_users()


def load_accounts():
    try:
        with open('accounts.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_accounts(accounts):
    with open('accounts.json', 'w') as f:
        json.dump(accounts, f, indent=2)


accounts_data = load_accounts()


@app.before_request
def check_authentication():
    # Exclude static folder from the authentication check
    if request.path.startswith('/static/') or request.path.startswith('/img/') or request.path.startswith(
            '/favicon.ico'):
        return
    if not current_user.is_authenticated and request.endpoint != 'login':
        print(f'Redirected request from {request.path}')
        return redirect(url_for('login'))


@app.route('/')
@login_required
def accounts():
    accounts_updated = False  # Add this line to track if any accounts were updated

    for i, account in enumerate(accounts_data):
        last_fetched = account.get("last_fetched", "Never")
        if last_fetched:
            last_fetched_dt = datetime.strptime(last_fetched, "%m/%d/%Y")
            if (datetime.now() - last_fetched_dt) >= timedelta(days=3):
                updated_account = fetch_account_details(account)
                accounts_data[i] = updated_account  # Update the accounts_data list with the updated account data
                accounts_updated = True  # Set accounts_updated to True if an account was updated
        else:
            updated_account = fetch_account_details(account)
            accounts_data[i] = updated_account  # Update the accounts_data list with the updated account data
            accounts_updated = True  # Set accounts_updated to True if an account was updated

    # Save the updated accounts to the JSON file if any accounts were updated
    if accounts_updated:
        save_accounts(accounts_data)

    return render_template('accounts.html', accounts=accounts_data)


@app.route('/add_account', methods=['GET'])
@login_required
def account_form():
    return render_template('account_form.html')


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
        "rank": "",
        "rr": "",
        "last_fetched": "01/01/1990"
    }
    accounts_data.append(new_account)
    save_accounts(accounts_data)
    return redirect(url_for('accounts'))


def fetch_account_details(account):
    print(f"Fetching account details for {account['display']['name']}#{account['display']['tag']}...")

    account.setdefault('rank', 'Unknown')
    account.setdefault('rr', '??')
    last_fetched = account.get("last_fetched", "01/01/1990")
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
            account['rr'] = rank_rr[1].removesuffix('RR.')
            account['last_fetched'] = now.strftime("%m/%d/%Y")
        else:
            print(f"Unexpected API response format: {response.text}")
    else:
        print(
            f"API request for {account['display']['name']}#{account['display']['tag']} failed with status code {response.status_code}")

    print(f"Fetching account details for {account['display']['name']}#{account['display']['tag']}... Done. :)")

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
