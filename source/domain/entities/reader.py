from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Callable, Optional, Any


@dataclass(slots=True)
class Reader:
    reader_id: str
    user_id: int
    full_name: str
    identity_number: str
    card_issue_date: date
    card_expiry_date: date
    dob: Optional[date] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    account_status: str = "ACTIVE"
    created_at: Optional[datetime] = None

    def view_profile(self) -> dict[str, Any]:
        """Return the reader's own profile fields without account secrets."""
        return {
            "reader_id": self.reader_id,
            "full_name": self.full_name,
            "dob": self.dob.isoformat() if self.dob else None,
            "gender": self.gender,
            "identity_number": self.identity_number,
            "phone": self.phone,
            "card_issue_date": self.card_issue_date.isoformat(),
            "card_expiry_date": self.card_expiry_date.isoformat(),
            "account_status": self.account_status,
        }

    def view_borrowing_history(
        self,
        history_loader: Callable[[str], list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        """Load borrowing history for this reader only.

        A loader is injected to keep the entity independent from SQL and Flask.
        The caller must provide a reader-scoped loader, not a global query.
        """
        return history_loader(self.reader_id)
