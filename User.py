import json
import os

from flask_login import UserMixin

MASTER_KEY = os.environ.get("master_key")


class User(UserMixin):
    def __init__(self, auth_key, name):
        self.id = auth_key
        self.name = name


def load_users(users_file):
    if not os.path.exists(users_file):
        default = f'{{ "{MASTER_KEY}": "Master" }}'
        save_users(users_file, json.loads(default))

    with open(users_file, 'r') as f:
        data = json.load(f)

    if MASTER_KEY not in data:
        data[MASTER_KEY] = "Master"

    users = {auth_key: User(auth_key, name) for auth_key, name in data.items()}
    return users


def save_users(users_file, users_json):
    if MASTER_KEY not in users_json:
        users_json[MASTER_KEY] = "Master"

    with open(users_file, 'w') as f:
        json.dump(users_json, f, indent=2)


def is_master(user):
    return user.id == MASTER_KEY
