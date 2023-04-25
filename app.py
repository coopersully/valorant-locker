import json
import os
import random
from datetime import datetime, timedelta

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy

from config import SECRET_KEY, DATABASE_PATH

load_dotenv()

# App
app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['SESSION_COOKIE_SECURE'] = True
app.config['REMEMBER_COOKIE_SECURE'] = True

# App database
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_PATH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from models import User
from models.User import is_master, hash_it
from models.ValorantAccount import ValorantAccount, fetch_account_details
from werkzeug.security import check_password_hash

# Login functionality
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

with app.app_context():
    db.create_all()


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

    if request.endpoint in ['login', 'register', 'access_denied']:
        return

    if not current_user.is_authenticated and request.endpoint != 'login':
        print(f'Redirected request from {request.path}')
        return redirect(url_for('login'))


# Favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


@app.route('/')
@login_required
def accounts():
    accounts_updated = False
    live_accounts = ValorantAccount.query.all()

    for account in live_accounts:
        last_fetched = account.last_updated
        if last_fetched:
            if (datetime.now() - account.last_updated) >= timedelta(days=3):
                fetch_account_details(account)
                accounts_updated = True
        else:
            accounts_updated = True

    if accounts_updated:
        live_accounts = ValorantAccount.query.all()

    return render_template('accounts.html', accounts=live_accounts)


# Show the form to add a new account
@app.route('/add_account', methods=['GET'])
@login_required
def account_form():
    return render_template('account_form.html')


@app.route('/add_account', methods=['POST'])
@login_required
def add_account():
    new_account = ValorantAccount(
        username=request.form['username'],
        password=request.form['password'],
        display_name=request.form['display_name'],
        display_tag=request.form['display_tag'],
        region=request.form['region']
    )
    db.session.add(new_account)
    db.session.commit()
    return redirect(url_for('accounts'))


@login_manager.user_loader
def load_user(user_id):
    return User.User.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        print(f'Attempting to log in with username: {username}')

        user = User.User.query.filter_by(username=username).first()

        if user:
            print(f'User found in the database: {user.username}')
            print(f'Stored password hash: {user.password}')
            print(f'Input password: {password}')
            print(f'Hash of input password: {hash_it(password)}')

            if check_password_hash(user.password, password):
                if user.permission_level >= 1 or is_master(user):
                    login_user(user)
                    flash('You have been logged in.', 'success')
                    print(f'User {username} logged in successfully.')
                    return redirect(url_for('accounts'))
                else:
                    flash('Access denied. Please contact the administrator.', 'danger')
                    print(f'User {username} access denied due to insufficient permission level.')
                    return redirect(url_for('access_denied'))
            else:
                flash('Invalid username or password.', 'danger')
                print(f'Invalid password for user {username}')
        else:
            flash('Invalid username or password.', 'danger')
            print(f'User {username} not found in the database')

        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        password = request.form['password']

        print(f'Attempting to register new user: {username}')

        existing_user = User.User.query.filter_by(username=username).first()

        if existing_user:
            flash('That username is already taken. Please choose a different one.', 'danger')
            print(f'Username {username} already exists.')
            return redirect(url_for('register'))

        new_user = User.User(email=email, first_name=first_name, last_name=last_name, username=username,
                             password=hash_it(password))

        db.session.add(new_user)
        db.session.commit()

        flash('Your account has been created!', 'success')
        print(f'User {username} registered successfully.')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/control-panel', methods=['GET', 'POST'])
@login_required
def control_panel():
    if not User.is_master(current_user):
        return redirect(url_for('access_denied'))

    if request.method == 'POST':
        users = User.User.query.all()
        for user in users:
            updated_username = request.form[f'username-{user.id}']
            updated_email = request.form[f'email-{user.id}']
            updated_first_name = request.form[f'first_name-{user.id}']
            updated_last_name = request.form[f'last_name-{user.id}']
            updated_permission_level = request.form[f'permission_level-{user.id}']

            user.username = updated_username
            user.email = updated_email
            user.first_name = updated_first_name
            user.last_name = updated_last_name
            user.permission_level = int(updated_permission_level)

        db.session.commit()
        flash('User information has been updated.', 'success')
        return redirect(url_for('control_panel'))

    users = User.User.query.all()
    return render_template('control_panel.html', users=users)


@app.route('/import-accounts', methods=['POST'])
@login_required
def import_accounts():
    if not is_master(current_user):
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
        for account_data in data:
            new_account = ValorantAccount(
                username=account_data['username'],
                password=account_data['password'],
                display_name=account_data['display']['name'],
                display_tag=account_data['display']['tag'],
                region=account_data['region']
            )
            db.session.add(new_account)
        db.session.commit()

        flash('Accounts imported successfully', 'success')
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


if __name__ == "__main__":
    app.run()
