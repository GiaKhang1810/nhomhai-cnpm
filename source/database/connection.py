from __future__ import annotations

from typing import Optional

from flask import current_app, g
from mysql.connector import Error, connect
from mysql.connector.connection import MySQLConnection


def get_db_connection() -> MySQLConnection:
    """Return one MySQL connection for the current Flask application context."""
    connection = g.get("db")
    if connection is None or not connection.is_connected():
        try:
            connection = connect(
                host=current_app.config["DB_HOST"],
                user=current_app.config["DB_USER"],
                password=current_app.config["DB_PASSWORD"],
                database=current_app.config["DB_NAME"],
                port=current_app.config["DB_PORT"],
                connection_timeout=current_app.config.get("DB_CONNECT_TIMEOUT", 10),
                charset="utf8mb4",
                collation="utf8mb4_unicode_ci",
                autocommit=True,
            )
            g.db = connection
        except Error:
            current_app.logger.exception("Unable to connect to MySQL")
            raise
    return connection


def close_db_connection(error: Optional[BaseException] = None) -> None:
    connection = g.pop("db", None)
    if connection is not None:
        try:
            if connection.is_connected():
                if error is not None:
                    connection.rollback()
                connection.close()
        except Error:
            current_app.logger.exception("Error while closing MySQL connection")
