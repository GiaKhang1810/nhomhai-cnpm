from __future__ import annotations

import os
import re
from getpass import getpass
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def main() -> None:
    username = input("Username: ").strip()
    email = input("Email: ").strip().lower()
    password = getpass("Password (at least 8 characters): ")
    confirm = getpass("Confirm password: ")

    if not username or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise SystemExit("Username and a valid email are required.")
    if len(password) < 8:
        raise SystemExit("Password must contain at least 8 characters.")
    if password != confirm:
        raise SystemExit("Passwords do not match.")

    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "library_db"),
        port=int(os.getenv("DB_PORT", "3306")),
        connection_timeout=int(os.getenv("DB_CONNECT_TIMEOUT", "10")),
        charset="utf8mb4",
    )
    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role, account_status) VALUES (%s, %s, %s, 'ADMIN', 'ACTIVE')",
            (username, email, generate_password_hash(password)),
        )
        connection.commit()
        print(f"Administrator created successfully. User ID: {cursor.lastrowid}")
    except mysql.connector.Error as error:
        connection.rollback()
        raise SystemExit(f"Unable to create administrator: {error}") from error
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
