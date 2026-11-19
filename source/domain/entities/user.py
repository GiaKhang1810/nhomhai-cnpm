from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class User:
    username: str
    email: str
    password_hash: str
    role: str
    account_status: str = "ACTIVE"
    user_id: Optional[int] = None

    @classmethod
    def login(
        cls,
        username_or_email: str,
        password: str,
        expected_role: str | None = None,
    ) -> Optional["User"]:
        """Authenticate through the application's authentication service.

        Authentication remains in AuthService so password verification and
        database access are not duplicated in the entity.
        """
        from source.services.auth_service import AuthService

        return AuthService().authenticate(username_or_email, password, expected_role)
