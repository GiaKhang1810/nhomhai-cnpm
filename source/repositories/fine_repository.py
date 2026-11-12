from __future__ import annotations

from decimal import Decimal
from typing import Any

from source.database.connection import get_db_connection


class FineRepository:
    def get_outstanding_charges(self, reader_id: str | None = None) -> list[dict[str, Any]]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        where = "" if not reader_id else "AND br.reader_id=%s"
        params = () if not reader_id else (reader_id,)
        try:
            cursor.execute(
                f"""SELECT bd.detail_id, bd.loan_id, bd.copy_id, r.reader_id, r.full_name,
                          b.title, bd.overdue_fine, bd.compensation,
                          COALESCE(SUM(fp.amount), 0) AS paid_amount,
                          (bd.overdue_fine + bd.compensation - COALESCE(SUM(fp.amount), 0)) AS outstanding
                   FROM borrowing_details bd
                   JOIN borrowing_records br ON br.loan_id=bd.loan_id
                   JOIN readers r ON r.reader_id=br.reader_id
                   JOIN book_copies bc ON bc.copy_id=bd.copy_id
                   JOIN books b ON b.book_code=bc.book_code
                   LEFT JOIN fine_payments fp ON fp.detail_id=bd.detail_id
                   WHERE bd.return_date IS NOT NULL {where}
                   GROUP BY bd.detail_id, bd.loan_id, bd.copy_id, r.reader_id, r.full_name,
                            b.title, bd.overdue_fine, bd.compensation, br.due_date
                   HAVING outstanding > 0
                   ORDER BY br.due_date, bd.detail_id""",
                params,
            )
            return cursor.fetchall()
        finally:
            cursor.close()

    def record_payment(
        self,
        detail_id: int,
        amount: Decimal,
        payment_method: str,
        received_by: int,
        note: str | None = None,
    ) -> tuple[bool, str]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            db.start_transaction()
            cursor.execute(
                """SELECT detail_id, return_date, overdue_fine, compensation
                   FROM borrowing_details WHERE detail_id=%s FOR UPDATE""",
                (detail_id,),
            )
            detail = cursor.fetchone()
            if not detail or detail["return_date"] is None:
                raise ValueError("Không tìm thấy khoản phí cần thanh toán.")
            cursor.execute("SELECT COALESCE(SUM(amount), 0) AS paid FROM fine_payments WHERE detail_id=%s", (detail_id,))
            paid = Decimal(str(cursor.fetchone()["paid"]))
            total_charge = Decimal(str(detail["overdue_fine"])) + Decimal(str(detail["compensation"]))
            outstanding = total_charge - paid
            if amount <= 0:
                raise ValueError("Số tiền thanh toán phải lớn hơn 0.")
            if amount > outstanding:
                raise ValueError(f"Số tiền vượt quá khoản còn phải trả ({outstanding:,.0f} VND).")
            cursor.execute(
                """INSERT INTO fine_payments (detail_id, amount, payment_method, received_by, note)
                   VALUES (%s, %s, %s, %s, %s)""",
                (detail_id, amount, payment_method, received_by, note),
            )
            db.commit()
            return True, "Ghi nhận thanh toán thành công."
        except ValueError as error:
            db.rollback()
            return False, str(error)
        except Exception:
            db.rollback()
            raise
        finally:
            cursor.close()
