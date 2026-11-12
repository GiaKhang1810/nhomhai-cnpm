from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

@dataclass
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
    account_status: str = 'ACTIVE'
    created_at: Optional[datetime] = None