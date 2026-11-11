from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    username: str
    email: str
    password_hash: str
    role: str
    account_status: str = 'ACTIVE'
    user_id: Optional[int] = None