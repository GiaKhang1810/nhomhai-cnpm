from dataclasses import dataclass
from datetime import date
from typing import List, Optional

@dataclass
class BorrowingDetail:
    copy_id: str
    detail_id: Optional[int] = None
    loan_id: Optional[str] = None
    return_date: Optional[date] = None
    overdue_fine: float = 0.0
    compensation: float = 0.0

@dataclass
class BorrowingRecord:
    loan_id: str
    reader_id: str
    borrow_date: date
    due_date: date
    status: str = 'BORROWED'
    details: List[BorrowingDetail] = None

    def __post_init__(self):
        if self.details is None:
            self.details = []