from __future__ import annotations

from typing import Optional

from source.core.security import verify_password
from source.database.connection import get_db_connection
from source.database.row_mapper import map_to_user
from source.domain.entities.user import User


class AuthService:
    def authenticate(self, username_or_email: str, password: str, expected_role: str | None = None) -> Optional[User]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM users WHERE username=%s OR email=%s LIMIT 1",
                (username_or_email, username_or_email),
            )
            row = cursor.fetchone()
        finally:
            cursor.close()
        if not row:
            return None
        user = map_to_user(row)
        if user.account_status != "ACTIVE":
            return None
        if expected_role and user.role != expected_role:
            return None
        return user if verify_password(password, user.password_hash) else None
