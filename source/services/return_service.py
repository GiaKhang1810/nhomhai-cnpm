from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Sequence

from source.repositories.return_repository import ReturnRepository


@dataclass(frozen=True, slots=True)
class ReturnItemRequest:
    copy_id: str
    condition: str = "NORMAL"


class ReturnService:
    def __init__(self) -> None:
        self.return_repo = ReturnRepository()

    def process_returns(
        self,
        loan_id: str,
        returned_items: Sequence[ReturnItemRequest],
    ) -> tuple[bool, str, Decimal]:
        if not loan_id.strip():
            return False, "Vui lòng nhập mã phiếu mượn.", Decimal("0.00")
        if not returned_items:
            return False, "Không có bản sao nào được chọn để trả.", Decimal("0.00")
        copy_ids = [item.copy_id.strip() for item in returned_items]
        if any(not copy_id for copy_id in copy_ids) or len(copy_ids) != len(set(copy_ids)):
            return False, "Mã bản sao bị thiếu hoặc trùng lặp.", Decimal("0.00")
        if any(item.condition not in {"NORMAL", "DAMAGED", "LOST"} for item in returned_items):
            return False, "Tình trạng sách trả không hợp lệ.", Decimal("0.00")
        try:
            success, total_charge, message = self.return_repo.process_return_transaction(
                loan_id.strip(), date.today(),
                [{"copy_id": item.copy_id.strip(), "condition": item.condition} for item in returned_items],
            )
            if success and total_charge > 0:
                message += f" Tổng phí phát sinh: {total_charge:,.0f} VND."
            return success, message, total_charge
        except Exception:
            return False, "Lỗi hệ thống khi ghi nhận trả sách. Giao dịch đã được hoàn tác.", Decimal("0.00")
