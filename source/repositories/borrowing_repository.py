from __future__ import annotations

from source.database.connection import get_db_connection
from source.domain.entities.borrowing import BorrowingRecord


class BorrowingRepository:
    def count_active_books_by_reader(self, reader_id: str) -> int:
        db = get_db_connection()
        cursor = db.cursor()
        try:
            cursor.execute(
                """SELECT COUNT(*) FROM borrowing_details bd
                   JOIN borrowing_records br ON br.loan_id=bd.loan_id
                   WHERE br.reader_id=%s AND bd.return_date IS NULL""",
                (reader_id,),
            )
            return int(cursor.fetchone()[0])
        finally:
            cursor.close()

    def has_overdue_books(self, reader_id: str) -> bool:
        db = get_db_connection()
        cursor = db.cursor()
        try:
            cursor.execute(
                """SELECT 1 FROM borrowing_records br
                   JOIN borrowing_details bd ON bd.loan_id=br.loan_id
                   WHERE br.reader_id=%s AND bd.return_date IS NULL
                     AND br.due_date < CURDATE() LIMIT 1""",
                (reader_id,),
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def create_loan_transaction(self, record: BorrowingRecord, request_id: str | None = None, processed_by: int | None = None) -> tuple[bool, str]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            db.start_transaction()
            cursor.execute("SELECT reader_id, account_status, card_expiry_date FROM readers WHERE reader_id=%s FOR UPDATE", (record.reader_id,))
            reader = cursor.fetchone()
            if not reader:
                raise ValueError("Không tìm thấy thông tin độc giả.")
            if request_id:
                cursor.execute(
                    "SELECT reader_id, status FROM borrow_requests WHERE request_id=%s FOR UPDATE",
                    (request_id,),
                )
                borrow_request = cursor.fetchone()
                if not borrow_request or borrow_request["reader_id"] != record.reader_id:
                    raise ValueError("Không tìm thấy yêu cầu mượn hợp lệ cho độc giả này.")
                if borrow_request["status"] != "PENDING":
                    raise ValueError("Yêu cầu mượn này đã được xử lý trước đó.")
            from datetime import date
            today = date.today()
            if reader["account_status"] != "ACTIVE" or reader["card_expiry_date"] < today:
                raise ValueError("Thẻ độc giả đã hết hạn hoặc bị khóa.")

            cursor.execute(
                """SELECT COUNT(*) AS total FROM borrowing_details bd
                   JOIN borrowing_records br ON br.loan_id=bd.loan_id
                   WHERE br.reader_id=%s AND bd.return_date IS NULL""",
                (record.reader_id,),
            )
            current_borrowed = int(cursor.fetchone()["total"])
            requested_count = len(record.details)
            if current_borrowed + requested_count > 5:
                raise ValueError(f"Độc giả chỉ được mượn tối đa 5 cuốn. Đang mượn: {current_borrowed}.")

            cursor.execute(
                """SELECT 1 FROM borrowing_records br
                   JOIN borrowing_details bd ON bd.loan_id=br.loan_id
                   WHERE br.reader_id=%s AND bd.return_date IS NULL
                     AND br.due_date < %s LIMIT 1""",
                (record.reader_id, today),
            )
            if cursor.fetchone():
                raise ValueError("Độc giả đang có sách quá hạn chưa trả, không thể mượn thêm.")

            copy_ids = [detail.copy_id for detail in record.details]
            if len(copy_ids) != len(set(copy_ids)):
                raise ValueError("Danh sách bản sao có mã bị trùng.")
            placeholders = ",".join(["%s"] * len(copy_ids))
            cursor.execute(
                f"SELECT DISTINCT book_code FROM book_copies WHERE copy_id IN ({placeholders}) ORDER BY book_code",
                tuple(copy_ids),
            )
            book_codes = [row["book_code"] for row in cursor.fetchall()]
            if book_codes:
                book_placeholders = ",".join(["%s"] * len(book_codes))
                cursor.execute(
                    f"SELECT book_code FROM books WHERE book_code IN ({book_placeholders}) AND is_active=TRUE ORDER BY book_code FOR UPDATE",
                    tuple(book_codes),
                )
                active_books = cursor.fetchall()
                if len(active_books) != len(book_codes):
                    raise ValueError("Đầu sách không còn được kinh doanh.")
            cursor.execute(
                f"""SELECT bc.copy_id, bc.book_code FROM book_copies bc
                    WHERE bc.copy_id IN ({placeholders}) AND bc.status='AVAILABLE'
                    FOR UPDATE""",
                tuple(copy_ids),
            )
            available = cursor.fetchall()
            if len(available) != len(copy_ids):
                raise ValueError("Một hoặc nhiều bản sao không tồn tại, đã được mượn hoặc không còn khả dụng.")

            cursor.execute(
                "INSERT INTO borrowing_records (loan_id, reader_id, borrow_date, due_date, status) VALUES (%s, %s, %s, %s, 'BORROWED')",
                (record.loan_id, record.reader_id, record.borrow_date, record.due_date),
            )
            cursor.executemany(
                "INSERT INTO borrowing_details (loan_id, copy_id) VALUES (%s, %s)",
                [(record.loan_id, copy_id) for copy_id in copy_ids],
            )
            cursor.executemany(
                "UPDATE book_copies SET status='BORROWED' WHERE copy_id=%s AND status='AVAILABLE'",
                [(copy_id,) for copy_id in copy_ids],
            )
            if cursor.rowcount != len(copy_ids):
                raise ValueError("Trạng thái bản sao vừa thay đổi. Vui lòng tải lại và thử lại.")

            counts: dict[str, int] = {}
            for row in available:
                counts[row["book_code"]] = counts.get(row["book_code"], 0) + 1
            for book_code, quantity in counts.items():
                cursor.execute(
                    "UPDATE books SET available_quantity=available_quantity-%s WHERE book_code=%s AND available_quantity >= %s",
                    (quantity, book_code, quantity),
                )
                if cursor.rowcount != 1:
                    raise ValueError("Số lượng tồn kho không nhất quán. Giao dịch đã được hủy.")
            if request_id:
                cursor.execute(
                    "UPDATE borrow_requests SET status='APPROVED', processed_by=%s, processed_at=NOW() WHERE request_id=%s AND status='PENDING'",
                    (processed_by, request_id),
                )
                if cursor.rowcount != 1:
                    raise ValueError("Yêu cầu mượn vừa được xử lý bởi giao dịch khác.")
            db.commit()
            return True, f"Tạo phiếu mượn thành công. Mã phiếu: {record.loan_id}"
        except ValueError as error:
            db.rollback()
            return False, str(error)
        except Exception:
            db.rollback()
            raise
        finally:
            cursor.close()
