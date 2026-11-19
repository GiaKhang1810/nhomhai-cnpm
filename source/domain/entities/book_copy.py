from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BookCopy:
    copy_id: str
    book_code: str
    condition: str = "NORMAL"
    status: str = "AVAILABLE"

    VALID_CONDITIONS = frozenset({"NORMAL", "DAMAGED", "LOST"})
    VALID_STATUSES = frozenset({"AVAILABLE", "BORROWED", "DAMAGED", "LOST", "RETIRED"})

    def update_status(self, status: str, condition: str | None = None) -> None:
        """Update a physical copy's status and condition consistently."""
        next_status = status.upper().strip()
        next_condition = (condition or self.condition).upper().strip()
        if next_status not in self.VALID_STATUSES:
            raise ValueError("Trạng thái bản sao không hợp lệ.")
        if next_condition not in self.VALID_CONDITIONS:
            raise ValueError("Tình trạng bản sao không hợp lệ.")
        if next_status == "AVAILABLE" and next_condition != "NORMAL":
            raise ValueError("Chỉ bản sao ở tình trạng bình thường mới có thể sẵn sàng cho mượn.")
        if next_status == "DAMAGED" and next_condition != "DAMAGED":
            raise ValueError("Bản sao ở trạng thái hỏng phải có tình trạng DAMAGED.")
        if next_status == "LOST" and next_condition != "LOST":
            raise ValueError("Bản sao ở trạng thái mất phải có tình trạng LOST.")
        self.status = next_status
        self.condition = next_condition
