import json

from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, auth_key, name):
        self.id = auth_key
        self.name = name


def load_users():
    with open('users.json', 'r') as f:
        data = json.load(f)
    users = {auth_key: User(auth_key, name) for auth_key, name in data.items()}
    return users

