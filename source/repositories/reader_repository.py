from __future__ import annotations

from typing import Any, Optional

from source.database.connection import get_db_connection
from source.domain.entities.reader import Reader


class ReaderRepository:
    def get_by_id(self, reader_id: str) -> Optional[Reader]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM readers WHERE reader_id = %s", (reader_id,))
            row = cursor.fetchone()
            return Reader(**row) if row else None
        finally:
            cursor.close()

    def get_by_user_id(self, user_id: int) -> Optional[Reader]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM readers WHERE user_id=%s", (user_id,))
            row = cursor.fetchone()
            return Reader(**row) if row else None
        finally:
            cursor.close()

    def search_readers(self, keyword: str) -> list[Reader]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        pattern = f"%{keyword.strip()}%"
        try:
            cursor.execute(
                """SELECT * FROM readers
                   WHERE reader_id LIKE %s OR full_name LIKE %s OR identity_number LIKE %s
                   ORDER BY full_name LIMIT 200""",
                (pattern, pattern, pattern),
            )
            return [Reader(**row) for row in cursor.fetchall()]
        finally:
            cursor.close()

    def create_reader_transaction(self, user_data: dict[str, Any], reader_data: dict[str, Any]) -> bool:
        db = get_db_connection()
        cursor = db.cursor()
        try:
            db.start_transaction()
            cursor.execute(
                """INSERT INTO users (username, email, password_hash, role, account_status)
                   VALUES (%s, %s, %s, 'READER', 'ACTIVE')""",
                (user_data["username"], user_data["email"], user_data["password_hash"]),
            )
            user_id = cursor.lastrowid
            cursor.execute(
                """INSERT INTO readers
                   (reader_id, user_id, full_name, dob, gender, identity_number, phone,
                    card_issue_date, card_expiry_date, account_status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'ACTIVE')""",
                (
                    reader_data["reader_id"], user_id, reader_data["full_name"],
                    reader_data.get("dob"), reader_data.get("gender"),
                    reader_data["identity_number"], reader_data.get("phone"),
                    reader_data["card_issue_date"], reader_data["card_expiry_date"],
                ),
            )
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise
        finally:
            cursor.close()

    def update_reader(self, reader_id: str, data: dict[str, Any]) -> tuple[bool, str]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            db.start_transaction()
            cursor.execute("SELECT * FROM readers WHERE reader_id=%s FOR UPDATE", (reader_id,))
            reader = cursor.fetchone()
            if not reader:
                db.rollback()
                return False, "Không tìm thấy độc giả."
            cursor.execute(
                """UPDATE readers SET full_name=%s, dob=%s, gender=%s,
                   identity_number=%s, phone=%s, card_expiry_date=%s
                   WHERE reader_id=%s""",
                (
                    data.get("full_name", reader["full_name"]),
                    data.get("dob", reader["dob"]),
                    data.get("gender", reader["gender"]),
                    data.get("identity_number", reader["identity_number"]),
                    data.get("phone", reader["phone"]),
                    data.get("card_expiry_date", reader["card_expiry_date"]),
                    reader_id,
                ),
            )
            db.commit()
            return True, "Cập nhật hồ sơ độc giả thành công."
        except Exception:
            db.rollback()
            raise
        finally:
            cursor.close()

    def deactivate_reader(self, reader_id: str) -> tuple[bool, str]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            db.start_transaction()
            cursor.execute("SELECT user_id FROM readers WHERE reader_id=%s FOR UPDATE", (reader_id,))
            reader = cursor.fetchone()
            if not reader:
                db.rollback()
                return False, "Không tìm thấy độc giả."
            cursor.execute(
                """SELECT COUNT(*) AS total FROM borrowing_details bd
                   JOIN borrowing_records br ON br.loan_id=bd.loan_id
                   WHERE br.reader_id=%s AND bd.return_date IS NULL""",
                (reader_id,),
            )
            if int(cursor.fetchone()["total"]) > 0:
                db.rollback()
                return False, "Không thể khóa độc giả khi vẫn còn sách chưa trả."
            cursor.execute(
                """SELECT bd.detail_id
                   FROM borrowing_details bd
                   JOIN borrowing_records br ON br.loan_id=bd.loan_id
                   LEFT JOIN (
                       SELECT detail_id, SUM(amount) AS paid_amount
                       FROM fine_payments GROUP BY detail_id
                   ) fp ON fp.detail_id=bd.detail_id
                   WHERE br.reader_id=%s AND bd.return_date IS NOT NULL
                     AND (bd.overdue_fine + bd.compensation - COALESCE(fp.paid_amount, 0)) > 0
                   LIMIT 1""",
                (reader_id,),
            )
            unpaid = cursor.fetchone()
            if unpaid:
                db.rollback()
                return False, "Không thể khóa độc giả khi vẫn còn khoản phạt hoặc bồi thường chưa thanh toán."
            cursor.execute("UPDATE readers SET account_status='INACTIVE' WHERE reader_id=%s", (reader_id,))
            cursor.execute("UPDATE users SET account_status='INACTIVE' WHERE user_id=%s", (reader["user_id"],))
            db.commit()
            return True, "Đã ngừng hoạt động thẻ độc giả."
        except Exception:
            db.rollback()
            raise
        finally:
            cursor.close()
