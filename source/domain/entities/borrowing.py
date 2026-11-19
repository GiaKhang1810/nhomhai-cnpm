from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import List, Optional

from source.core.money import calculate_overdue_fine


@dataclass(slots=True)
class BorrowingDetail:
    copy_id: str
    detail_id: Optional[int] = None
    loan_id: Optional[str] = None
    return_date: Optional[date] = None
    overdue_fine: Decimal = Decimal("0.00")
    compensation: Decimal = Decimal("0.00")

    def calculate_fine(
        self,
        due_date: date,
        return_date: date,
        *,
        condition: str = "NORMAL",
        listed_value: Decimal = Decimal("0.00"),
    ) -> Decimal:
        """Calculate the overdue fine and any lost/damaged-copy compensation."""
        normalized_condition = condition.upper().strip()
        if normalized_condition not in {"NORMAL", "DAMAGED", "LOST"}:
            raise ValueError("Tình trạng sách trả không hợp lệ.")
        value = Decimal(str(listed_value))
        if not value.is_finite() or value < 0:
            raise ValueError("Giá trị niêm yết để tính bồi thường không hợp lệ.")

        self.return_date = return_date
        self.overdue_fine = calculate_overdue_fine(due_date, return_date)
        self.compensation = value if normalized_condition in {"DAMAGED", "LOST"} else Decimal("0.00")
        return self.overdue_fine + self.compensation


@dataclass(slots=True)
class BorrowingRecord:
    loan_id: str
    reader_id: str
    borrow_date: date
    due_date: date
    status: str = "BORROWED"
    details: List[BorrowingDetail] = field(default_factory=list)

    def add_detail(self, detail: BorrowingDetail) -> None:
        if any(existing.copy_id == detail.copy_id for existing in self.details):
            raise ValueError("Không thể thêm trùng bản sao vào cùng một phiếu mượn.")
        self.details.append(detail)

    def is_fully_returned(self) -> bool:
        return bool(self.details) and all(detail.return_date is not None for detail in self.details)
