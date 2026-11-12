from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from mysql.connector.connection import MySQLConnection


@contextmanager
def transaction(connection: MySQLConnection) -> Iterator[None]:
    """Commit on success and rollback on every exception."""
    connection.start_transaction()
    try:
        yield
        connection.commit()
    except Exception:
        connection.rollback()
        raise
