from __future__ import annotations

from datetime import date, timedelta
from typing import Sequence
from uuid import uuid4

from source.domain.entities.borrowing import BorrowingDetail, BorrowingRecord
from source.repositories.borrowing_repository import BorrowingRepository


class BorrowingService:
    def __init__(self) -> None:
        self.borrowing_repo = BorrowingRepository()

    def process_borrowing(self, reader_id: str, copy_ids: Sequence[str]) -> tuple[bool, str]:
        if not reader_id.strip():
            return False, "Vui lòng cung cấp mã độc giả."
        if not copy_ids:
            return False, "Vui lòng chọn ít nhất một bản sao để mượn."
        if len(copy_ids) > 5:
            return False, "Mỗi giao dịch không thể mượn quá 5 bản sao."
        if any(not isinstance(copy_id, str) or not copy_id.strip() for copy_id in copy_ids):
            return False, "Mã bản sao không hợp lệ."
        if len(set(copy_ids)) != len(copy_ids):
            return False, "Danh sách mã bản sao không được trùng lặp."

        today = date.today()
        record = BorrowingRecord(
            loan_id=f"BR-{uuid4().hex[:10].upper()}",
            reader_id=reader_id.strip(),
            borrow_date=today,
            due_date=today + timedelta(days=14),
            details=[BorrowingDetail(copy_id=copy_id.strip()) for copy_id in copy_ids],
        )
        try:
            return self.borrowing_repo.create_loan_transaction(record)
        except Exception:
            return False, "Lỗi hệ thống khi tạo phiếu mượn. Giao dịch đã được hoàn tác."
