import json
import os
import random
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, login_required, login_user, logout_user, current_user

import User
from Account import load_accounts, save_accounts
from User import load_users

load_dotenv()

# App
app = Flask(__name__)
app.secret_key = os.environ.get("secret_key")

# Login functionality
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Storage files
USERS_FILE = os.environ.get("users_path")
live_users = load_users(USERS_FILE)

ACCOUNTS_FILE = os.environ.get("accounts_path")
live_accounts = load_accounts(ACCOUNTS_FILE)

# Account defaults
DEFAULT_LAST_FETCHED = "01/01/1990"
DEFAULT_RANK = "Unknown"
DEFAULT_RR = "??"


# Check user authentication before each request
@app.before_request
def check_authentication():
    # Exclude static folder from the authentication check
    if request.path.__contains__('.svg')\
            or request.path.__contains__('.png')\
            or request.path.__contains__('.jpg')\
            or request.path.__contains__('.css')\
            or request.path.__contains__('.ico'):
        return

    if not current_user.is_authenticated and request.endpoint != 'login':
        print(f'Redirected request from {request.path}')
        return redirect(url_for('login'))


# Favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


# Display accounts and update them if necessary
@app.route('/')
@login_required
def accounts():
    accounts_updated = False

    for i, account in enumerate(live_accounts):
        last_fetched = account.get("last_fetched", DEFAULT_LAST_FETCHED)
        if last_fetched:
            last_fetched_dt = datetime.strptime(last_fetched, "%m/%d/%Y")
            if (datetime.now() - last_fetched_dt) >= timedelta(days=3):
                updated_account = fetch_account_details(account)
                live_accounts[i] = updated_account
                accounts_updated = True
        else:
            updated_account = fetch_account_details(account)
            live_accounts[i] = updated_account
            accounts_updated = True

    if accounts_updated:
        save_accounts(ACCOUNTS_FILE, live_accounts)

    return render_template('accounts.html', accounts=live_accounts)


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
    live_accounts.append(new_account)
    save_accounts(ACCOUNTS_FILE, live_accounts)
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


@login_manager.user_loader
def load_user(auth_key):
    return live_users.get(auth_key)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        print('User is attempting to login.')
        auth_key = request.form['auth_key']
        user = live_users.get(auth_key)
        if user:
            print('Success! Logging in...')
            login_user(user)
            return redirect(url_for('accounts'))
        else:
            print('Failure! Invalid credentials.')
            flash('Invalid authentication key.', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/control-panel')
@login_required
def control_panel():
    if not User.is_master(current_user):
        return redirect(url_for('nope'))
    return render_template('control_panel.html')


@app.route('/import-accounts', methods=['POST'])
@login_required
def import_accounts():
    if not User.is_master(current_user):
        return

    file = request.files['accountsFile']
    print(f'{file}\n{type(file)}')

    if not file:
        flash('No file uploaded', 'danger')
        return redirect(url_for('control_panel'))

    if file.filename.rsplit('.', 1)[1].lower() != 'json':
        flash('Invalid file type. Please upload a JSON file.', 'danger')
        return redirect(url_for('control_panel'))

    try:
        data = json.load(file)
        save_accounts(ACCOUNTS_FILE, data)

        global live_accounts
        live_accounts = load_accounts(ACCOUNTS_FILE)

        flash('Accounts imported successfully', 'success')
    except json.JSONDecodeError:
        flash('Invalid JSON file. Please check the file and try again.', 'danger')

    return redirect(url_for('control_panel'))


@app.route('/import-users', methods=['POST'])
@login_required
def import_users():
    if not User.is_master(current_user):
        return

    file = request.files['usersFile']
    if not file:
        flash('No file uploaded', 'danger')
        return redirect(url_for('control_panel'))

    if file.filename.rsplit('.', 1)[1].lower() != 'json':
        flash('Invalid file type. Please upload a JSON file.', 'danger')
        return redirect(url_for('control_panel'))

    try:
        data = json.load(file)
        User.save_users(USERS_FILE, data)

        global live_users
        live_users = load_users(USERS_FILE)

        flash('Users imported successfully', 'success')
    except json.JSONDecodeError:
        flash('Invalid JSON file. Please check the file and try again.', 'danger')

    return redirect(url_for('control_panel'))


@app.route('/nope')
def access_denied():
    subtitles = [
        "lol get scammed",
        "sike u thought",
        "nice try, buster",
        "u just walked the prank",
        "skill issue",
        "back to the gulag"
    ]
    subtitle = random.choice(subtitles)
    return render_template('nope.html', subtitle=subtitle)


if __name__ == '__main__':
    app.run(debug=True)
