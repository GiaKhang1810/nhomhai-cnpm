
import os
from getpass import getpass

import mysql.connector
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()


def main():
    username = input("Username: ").strip()
    email = input("Email: ").strip()
    password = getpass("Password: ")
    confirm = getpass("Confirm password: ")

    if not username or not email or not password:
        raise ValueError("All fields are required.")

    if password != confirm:
        raise ValueError("Passwords do not match.")

    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306))
    )

    try:
        cursor = connection.cursor()

        password_hash = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO users (
                username,
                email,
                password_hash,
                role,
                account_status
            )
            VALUES (%s, %s, %s, 'ADMIN', 'ACTIVE')
            """,
            (username, email, password_hash)
        )

        connection.commit()

        print(f"Admin created successfully! ID: {cursor.lastrowid}")

    except mysql.connector.Error:
        connection.rollback()
        raise

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


if __name__ == "__main__":
    main()
