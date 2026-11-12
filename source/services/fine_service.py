from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from source.repositories.fine_repository import FineRepository


class FineService:
    def __init__(self) -> None:
        self.fine_repo = FineRepository()

    def get_outstanding_charges(self, reader_id: str | None = None) -> list[dict[str, Any]]:
        return self.fine_repo.get_outstanding_charges(reader_id)

    def record_payment(self, data: dict[str, Any], received_by: int) -> tuple[bool, str]:
        try:
            detail_id = int(data.get("detail_id"))
            amount = Decimal(str(data.get("amount")))
            if not amount.is_finite():
                return False, "Số tiền thanh toán không hợp lệ."
            method = str(data.get("payment_method", "CASH")).upper().strip()
            note = str(data.get("note", "")).strip() or None
            if method not in {"CASH", "BANK_TRANSFER", "CARD", "OTHER"}:
                return False, "Phương thức thanh toán không hợp lệ."
            if amount.as_tuple().exponent < -2:
                return False, "Số tiền chỉ được có tối đa hai chữ số thập phân."
            return self.fine_repo.record_payment(detail_id, amount, method, received_by, note)
        except (ValueError, TypeError, InvalidOperation):
            return False, "Mã khoản phí hoặc số tiền thanh toán không hợp lệ."
        except Exception:
            return False, "Không thể ghi nhận thanh toán. Vui lòng thử lại."
