import json
import os
import random
from datetime import datetime, timedelta

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, login_required, login_user, logout_user, current_user

from config import USERS_FILE, ACCOUNTS_FILE, SECRET_KEY, DEFAULT_LAST_FETCHED, DEFAULT_RR, DEFAULT_RANK
from models import User
from models.ValorantAccount import load_accounts, save_accounts, fetch_account_details
from models.User import load_users

load_dotenv()

# App
app = Flask(__name__)
app.secret_key = SECRET_KEY

# Login functionality
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Storage files
live_users = load_users(USERS_FILE)
live_accounts = load_accounts(ACCOUNTS_FILE)


# Check user authentication before each request
@app.before_request
def check_authentication():
    # Exclude static folder from the authentication check
    if request.path.__contains__('.svg') \
            or request.path.__contains__('.png') \
            or request.path.__contains__('.jpg') \
            or request.path.__contains__('.css') \
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
