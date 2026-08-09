"""Simple JSON-based authentication."""

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_PATH = os.path.join(BASE_DIR, "data", "credentials.json")


def load_credentials():
    """Read user credentials from data/credentials.json."""
    if not os.path.exists(CREDENTIALS_PATH):
        return {}
    with open(CREDENTIALS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def verify_login(username, password):
    
    credentials = load_credentials()
    user = credentials.get(username)

    if user is None:
        return None

    if user.get("password") != password:
        return None

    return {
        "username": username,
        "role": user.get("role"),
        "display_name": user.get("display_name", username),
    }
