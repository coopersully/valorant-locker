from flask_login import UserMixin
from werkzeug.security import generate_password_hash

from app import db
from config import MASTER_KEY


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    permission_level = db.Column(db.Integer, nullable=False, default=0)

    def __init__(self, email, first_name, last_name, username, password):
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.password = password
        self.permission_level = 0


def is_master(user):
    print(f'Is {user.username} == {MASTER_KEY}?')
    return user.username == MASTER_KEY


def hash_it(password):
    return generate_password_hash(password, method="sha256")
