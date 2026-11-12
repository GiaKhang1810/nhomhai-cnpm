from __future__ import annotations

from uuid import uuid4
from typing import Any

from source.database.connection import get_db_connection


class RequestRepository:
    def create_borrow_request(self, reader_id: str, book_code: str, quantity: int) -> tuple[bool, str, str | None]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        request_id = f"BRQ-{uuid4().hex[:10].upper()}"
        try:
            db.start_transaction()
            cursor.execute(
                "SELECT reader_id, account_status, card_expiry_date FROM readers WHERE reader_id=%s FOR UPDATE",
                (reader_id,),
            )
            reader = cursor.fetchone()
            if not reader:
                raise ValueError("Không tìm thấy hồ sơ độc giả.")
            cursor.execute("SELECT CURRENT_DATE AS today")
            today = cursor.fetchone()["today"]
            if reader["account_status"] != "ACTIVE" or reader["card_expiry_date"] < today:
                raise ValueError("Thẻ độc giả đã hết hạn hoặc đang bị khóa.")

            cursor.execute(
                """SELECT 1 FROM borrowing_records br
                   JOIN borrowing_details bd ON bd.loan_id=br.loan_id
                   WHERE br.reader_id=%s AND bd.return_date IS NULL AND br.due_date < %s LIMIT 1""",
                (reader_id, today),
            )
            if cursor.fetchone():
                raise ValueError("Bạn đang có sách quá hạn chưa trả nên chưa thể gửi yêu cầu mượn.")

            cursor.execute(
                """SELECT COUNT(*) AS total FROM borrowing_details bd
                   JOIN borrowing_records br ON br.loan_id=bd.loan_id
                   WHERE br.reader_id=%s AND bd.return_date IS NULL""",
                (reader_id,),
            )
            active_count = int(cursor.fetchone()["total"])
            cursor.execute(
                """SELECT COALESCE(SUM(bri.quantity), 0) AS total
                   FROM borrow_requests brq
                   JOIN borrow_request_items bri ON bri.request_id=brq.request_id
                   WHERE brq.reader_id=%s AND brq.status='PENDING'""",
                (reader_id,),
            )
            pending_count = int(cursor.fetchone()["total"])
            if active_count + pending_count + quantity > 5:
                raise ValueError("Tổng số sách đang mượn và chờ duyệt không được vượt quá 5 bản sao.")

            cursor.execute(
                "SELECT book_code, title, available_quantity, is_active FROM books WHERE book_code=%s FOR UPDATE",
                (book_code,),
            )
            book = cursor.fetchone()
            if not book or not book["is_active"]:
                raise ValueError("Đầu sách không tồn tại hoặc đã ngừng lưu hành.")
            if int(book["available_quantity"]) < quantity:
                raise ValueError("Số lượng sách khả dụng hiện không đủ. Vui lòng tải lại danh mục.")

            cursor.execute(
                "INSERT INTO borrow_requests (request_id, reader_id, status) VALUES (%s, %s, 'PENDING')",
                (request_id, reader_id),
            )
            cursor.execute(
                "INSERT INTO borrow_request_items (request_id, book_code, quantity) VALUES (%s, %s, %s)",
                (request_id, book_code, quantity),
            )
            db.commit()
            return True, f"Đã gửi yêu cầu mượn '{book['title']}'. Vui lòng chờ thủ thư xác nhận.", request_id
        except ValueError as error:
            db.rollback()
            return False, str(error), None
        except Exception:
            db.rollback()
            raise
        finally:
            cursor.close()

    def create_return_request(self, reader_id: str, detail_id: int) -> tuple[bool, str, str | None]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        request_id = f"RRQ-{uuid4().hex[:10].upper()}"
        try:
            db.start_transaction()
            cursor.execute(
                """SELECT bd.detail_id, bd.return_date, br.loan_id
                   FROM borrowing_details bd
                   JOIN borrowing_records br ON br.loan_id=bd.loan_id
                   WHERE bd.detail_id=%s AND br.reader_id=%s FOR UPDATE""",
                (detail_id, reader_id),
            )
            detail = cursor.fetchone()
            if not detail:
                raise ValueError("Không tìm thấy bản sao trong lịch sử mượn của bạn.")
            if detail["return_date"] is not None:
                raise ValueError("Bản sao này đã được thủ thư ghi nhận trả.")
            cursor.execute(
                "SELECT return_request_id FROM return_requests WHERE detail_id=%s AND status='PENDING' LIMIT 1 FOR UPDATE",
                (detail_id,),
            )
            if cursor.fetchone():
                raise ValueError("Bạn đã gửi yêu cầu trả cho bản sao này và đang chờ thủ thư xử lý.")
            cursor.execute(
                "INSERT INTO return_requests (return_request_id, reader_id, detail_id, status) VALUES (%s, %s, %s, 'PENDING')",
                (request_id, reader_id, detail_id),
            )
            db.commit()
            return True, "Đã gửi yêu cầu trả sách. Vui lòng mang sách đến quầy để thủ thư kiểm tra và xác nhận.", request_id
        except ValueError as error:
            db.rollback()
            return False, str(error), None
        except Exception:
            db.rollback()
            raise
        finally:
            cursor.close()

    def cancel_borrow_request(self, reader_id: str, request_id: str) -> tuple[bool, str]:
        db = get_db_connection()
        cursor = db.cursor()
        try:
            cursor.execute(
                "UPDATE borrow_requests SET status='CANCELLED', processed_at=NOW() WHERE request_id=%s AND reader_id=%s AND status='PENDING'",
                (request_id, reader_id),
            )
            if cursor.rowcount != 1:
                return False, "Không thể hủy yêu cầu. Yêu cầu có thể đã được thủ thư xử lý."
            return True, "Đã hủy yêu cầu mượn sách."
        finally:
            cursor.close()

    def cancel_return_request(self, reader_id: str, request_id: str) -> tuple[bool, str]:
        db = get_db_connection()
        cursor = db.cursor()
        try:
            cursor.execute(
                "UPDATE return_requests SET status='CANCELLED', processed_at=NOW() WHERE return_request_id=%s AND reader_id=%s AND status='PENDING'",
                (request_id, reader_id),
            )
            if cursor.rowcount != 1:
                return False, "Không thể hủy yêu cầu trả. Yêu cầu có thể đã được thủ thư xử lý."
            return True, "Đã hủy yêu cầu trả sách."
        finally:
            cursor.close()

    def get_pending_borrow_request(self, request_id: str) -> dict[str, Any] | None:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT request_id, reader_id, status FROM borrow_requests WHERE request_id=%s",
                (request_id,),
            )
            request = cursor.fetchone()
            if not request:
                return None
            cursor.execute(
                "SELECT book_code, quantity FROM borrow_request_items WHERE request_id=%s ORDER BY book_code",
                (request_id,),
            )
            request["items"] = cursor.fetchall()
            return request
        finally:
            cursor.close()

    def reject_borrow_request(self, request_id: str, processed_by: int, note: str = "") -> tuple[bool, str]:
        db = get_db_connection()
        cursor = db.cursor()
        try:
            db.start_transaction()
            cursor.execute("SELECT status FROM borrow_requests WHERE request_id=%s FOR UPDATE", (request_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError("Không tìm thấy yêu cầu mượn.")
            if row[0] != "PENDING":
                raise ValueError("Yêu cầu này đã được xử lý.")
            cursor.execute(
                "UPDATE borrow_requests SET status='REJECTED', processed_by=%s, processed_at=NOW(), staff_note=%s WHERE request_id=%s",
                (processed_by, note[:500], request_id),
            )
            db.commit()
            return True, "Đã từ chối yêu cầu mượn sách."
        except ValueError as error:
            db.rollback()
            return False, str(error)
        except Exception:
            db.rollback()
            raise
        finally:
            cursor.close()

    def reject_return_request(self, request_id: str, processed_by: int, note: str = "") -> tuple[bool, str]:
        db = get_db_connection()
        cursor = db.cursor()
        try:
            db.start_transaction()
            cursor.execute("SELECT status FROM return_requests WHERE return_request_id=%s FOR UPDATE", (request_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError("Không tìm thấy yêu cầu trả sách.")
            if row[0] != "PENDING":
                raise ValueError("Yêu cầu này đã được xử lý.")
            cursor.execute(
                "UPDATE return_requests SET status='REJECTED', processed_by=%s, processed_at=NOW(), staff_note=%s WHERE return_request_id=%s",
                (processed_by, note[:500], request_id),
            )
            db.commit()
            return True, "Đã từ chối yêu cầu trả sách."
        except ValueError as error:
            db.rollback()
            return False, str(error)
        except Exception:
            db.rollback()
            raise
        finally:
            cursor.close()
