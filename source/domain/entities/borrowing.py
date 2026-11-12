from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import List, Optional


@dataclass(slots=True)
class BorrowingDetail:
    copy_id: str
    detail_id: Optional[int] = None
    loan_id: Optional[str] = None
    return_date: Optional[date] = None
    overdue_fine: Decimal = Decimal("0.00")
    compensation: Decimal = Decimal("0.00")


@dataclass(slots=True)
class BorrowingRecord:
    loan_id: str
    reader_id: str
    borrow_date: date
    due_date: date
    status: str = "BORROWED"
    details: List[BorrowingDetail] = field(default_factory=list)
