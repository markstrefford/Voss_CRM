"""
Reset a user's password in Voss CRM.

Usage:
    cd backend && python -m scripts.reset_password <username> [password]

If no password is provided, a random one will be generated.
"""

import os
import secrets
import string
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.auth import hash_password
from app.services.sheet_service import users_sheet


def generate_password(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.reset_password <username> [password]")
        sys.exit(1)

    username = sys.argv[1]
    new_password = sys.argv[2] if len(sys.argv) > 2 else generate_password()

    user = users_sheet.find_by_field("username", username)
    if not user:
        print(f"User '{username}' not found.")
        sys.exit(1)

    users_sheet.update(user["id"], {"password_hash": hash_password(new_password)})
    print(f"Password reset for '{username}'.")
    print(f"New password: {new_password}")


if __name__ == "__main__":
    main()
