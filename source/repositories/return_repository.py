from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from source.core.money import calculate_overdue_fine
from source.database.connection import get_db_connection


class ReturnRepository:
    def get_loan_info(self, loan_id: str) -> dict[str, Any] | None:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT loan_id, reader_id, due_date, status FROM borrowing_records WHERE loan_id=%s",
                (loan_id,),
            )
            return cursor.fetchone()
        finally:
            cursor.close()

    def get_loan_details(self, loan_id: str) -> list[dict[str, Any]]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT bd.copy_id, bd.return_date, bd.overdue_fine, bd.compensation,
                          bc.book_code, b.title, bc.status AS copy_status
                   FROM borrowing_details bd
                   JOIN book_copies bc ON bc.copy_id=bd.copy_id
                   JOIN books b ON b.book_code=bc.book_code
                   WHERE bd.loan_id=%s ORDER BY bd.detail_id""",
                (loan_id,),
            )
            return cursor.fetchall()
        finally:
            cursor.close()

    def process_return_transaction(
        self,
        loan_id: str,
        return_date: date,
        items: list[dict[str, str]],
        processed_by: int | None = None,
    ) -> tuple[bool, Decimal, str]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            db.start_transaction()
            copy_ids = [item["copy_id"] for item in items]
            placeholders = ",".join(["%s"] * len(copy_ids))
            cursor.execute(
                f"SELECT DISTINCT book_code FROM book_copies WHERE copy_id IN ({placeholders}) ORDER BY book_code",
                tuple(copy_ids),
            )
            book_codes = [row["book_code"] for row in cursor.fetchall()]
            if book_codes:
                book_placeholders = ",".join(["%s"] * len(book_codes))
                cursor.execute(
                    f"SELECT book_code FROM books WHERE book_code IN ({book_placeholders}) ORDER BY book_code FOR UPDATE",
                    tuple(book_codes),
                )
                cursor.fetchall()

            cursor.execute(
                "SELECT loan_id, due_date FROM borrowing_records WHERE loan_id=%s FOR UPDATE",
                (loan_id,),
            )
            loan = cursor.fetchone()
            if not loan:
                raise ValueError("Không tìm thấy thông tin phiếu mượn.")

            total_charge = Decimal("0.00")
            for item in items:
                condition = item["condition"]
                if condition not in {"NORMAL", "DAMAGED", "LOST"}:
                    raise ValueError("Tình trạng sách trả không hợp lệ.")

                cursor.execute(
                    """SELECT bd.detail_id, bd.return_date, bc.copy_id, bc.book_code,
                              bc.status, b.listed_value
                       FROM borrowing_details bd
                       JOIN book_copies bc ON bc.copy_id=bd.copy_id
                       JOIN books b ON b.book_code=bc.book_code
                       WHERE bd.loan_id=%s AND bd.copy_id=%s FOR UPDATE""",
                    (loan_id, item["copy_id"]),
                )
                copy_info = cursor.fetchone()
                if not copy_info:
                    raise ValueError(f"Bản sao {item['copy_id']} không thuộc phiếu mượn này.")
                if copy_info["return_date"] is not None:
                    raise ValueError(f"Bản sao {item['copy_id']} đã được ghi nhận trả trước đó.")
                if copy_info["status"] != "BORROWED":
                    raise ValueError(f"Trạng thái bản sao {item['copy_id']} không hợp lệ để trả.")

                fine = calculate_overdue_fine(loan["due_date"], return_date)
                compensation = Decimal(str(copy_info["listed_value"])) if condition in {"DAMAGED", "LOST"} else Decimal("0.00")
                new_status = "AVAILABLE" if condition == "NORMAL" else condition

                cursor.execute(
                    """UPDATE borrowing_details SET return_date=%s, overdue_fine=%s, compensation=%s
                       WHERE detail_id=%s AND return_date IS NULL""",
                    (return_date, fine, compensation, copy_info["detail_id"]),
                )
                if cursor.rowcount != 1:
                    raise ValueError(f"Bản sao {item['copy_id']} đã được xử lý bởi một giao dịch khác.")
                cursor.execute(
                    "UPDATE book_copies SET status=%s, `condition`=%s WHERE copy_id=%s AND status='BORROWED'",
                    (new_status, condition, item["copy_id"]),
                )
                if cursor.rowcount != 1:
                    raise ValueError(f"Không thể cập nhật trạng thái bản sao {item['copy_id']}.")
                if new_status == "AVAILABLE":
                    cursor.execute(
                        "UPDATE books SET available_quantity=available_quantity+1 WHERE book_code=%s AND available_quantity < total_quantity",
                        (copy_info["book_code"],),
                    )
                    if cursor.rowcount != 1:
                        raise ValueError("Số lượng sách khả dụng không nhất quán. Giao dịch đã được hủy.")
                cursor.execute(
                    """UPDATE return_requests
                       SET status='COMPLETED', processed_by=%s, processed_at=NOW()
                       WHERE detail_id=%s AND status='PENDING'""",
                    (processed_by, copy_info["detail_id"]),
                )
                total_charge += fine + compensation

            cursor.execute(
                "SELECT COUNT(*) AS total FROM borrowing_details WHERE loan_id=%s AND return_date IS NULL",
                (loan_id,),
            )
            unreturned = int(cursor.fetchone()["total"])
            if unreturned == 0:
                status = "RETURNED"
            elif loan["due_date"] < return_date:
                status = "OVERDUE"
            else:
                status = "BORROWED"
            cursor.execute("UPDATE borrowing_records SET status=%s WHERE loan_id=%s", (status, loan_id))
            db.commit()
            return True, total_charge, "Ghi nhận trả sách thành công."
        except ValueError as error:
            db.rollback()
            return False, Decimal("0.00"), str(error)
        except Exception:
            db.rollback()
            raise
        finally:
            cursor.close()
