from __future__ import annotations

from typing import Any, Optional
from uuid import uuid4

from source.database.connection import get_db_connection
from source.database.row_mapper import map_to_book
from source.domain.entities.book import Book


class BookRepository:
    def get_by_code(self, book_code: str) -> Optional[Book]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM books WHERE book_code = %s", (book_code,))
            row = cursor.fetchone()
            return map_to_book(row) if row else None
        finally:
            cursor.close()

    def search_books(self, keyword: str, *, include_inactive: bool = False) -> list[Book]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        pattern = f"%{keyword.strip()}%"
        active_filter = "" if include_inactive else "AND is_active = TRUE"
        try:
            cursor.execute(
                f"""SELECT * FROM books
                    WHERE (title LIKE %s OR author LIKE %s OR book_code LIKE %s)
                    {active_filter}
                    ORDER BY title LIMIT 200""",
                (pattern, pattern, pattern),
            )
            return [map_to_book(row) for row in cursor.fetchall()]
        finally:
            cursor.close()


    def list_available_copies(self, book_code: str) -> list[dict[str, str]]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT copy_id, `condition`, status FROM book_copies WHERE book_code=%s AND status='AVAILABLE' ORDER BY copy_id",
                (book_code,),
            )
            return cursor.fetchall()
        finally:
            cursor.close()

    def create(self, book: Book) -> bool:
        """Insert a title and its physical copies in one transaction."""
        db = get_db_connection()
        cursor = db.cursor()
        try:
            db.start_transaction()
            cursor.execute(
                """INSERT INTO books
                   (book_code, title, author, publisher, publication_year, category,
                    listed_value, total_quantity, available_quantity, is_active)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)""",
                (book.book_code, book.title, book.author, book.publisher,
                 book.publication_year, book.category, book.listed_value,
                 book.total_quantity, book.total_quantity),
            )
            self._insert_copies(cursor, book.book_code, book.total_quantity)
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise
        finally:
            cursor.close()

    def update(self, book_code: str, data: dict[str, Any]) -> tuple[bool, str]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            db.start_transaction()
            cursor.execute("SELECT * FROM books WHERE book_code = %s FOR UPDATE", (book_code,))
            current = cursor.fetchone()
            if not current:
                db.rollback()
                return False, "Không tìm thấy đầu sách."

            new_total = int(data.get("total_quantity", current["total_quantity"]))
            if new_total < 0:
                db.rollback()
                return False, "Số lượng sách không hợp lệ."

            cursor.execute(
                "SELECT copy_id FROM book_copies WHERE book_code = %s AND status IN ('BORROWED', 'DAMAGED', 'LOST') FOR UPDATE",
                (book_code,),
            )
            unavailable_count = len(cursor.fetchall())
            if new_total < unavailable_count:
                db.rollback()
                return False, f"Không thể giảm số lượng thấp hơn số bản sao đang mượn/hỏng/mất ({unavailable_count})."

            cursor.execute(
                "SELECT copy_id FROM book_copies WHERE book_code = %s AND status = 'AVAILABLE' FOR UPDATE",
                (book_code,),
            )
            available_copy_ids = [row["copy_id"] for row in cursor.fetchall()]
            if new_total > current["total_quantity"]:
                self._insert_copies(cursor, book_code, new_total - int(current["total_quantity"]))
            elif new_total < current["total_quantity"]:
                remove_count = int(current["total_quantity"]) - new_total
                removable = sorted(available_copy_ids)[:remove_count]
                if len(removable) < remove_count:
                    db.rollback()
                    return False, "Không đủ bản sao khả dụng để giảm số lượng."
                placeholders = ",".join(["%s"] * len(removable))
                cursor.execute(
                    f"UPDATE book_copies SET status='RETIRED' WHERE copy_id IN ({placeholders}) AND status='AVAILABLE'",
                    tuple(removable),
                )
                if cursor.rowcount != len(removable):
                    raise ValueError("Không thể ngừng lưu hành một hoặc nhiều bản sao.")

            cursor.execute(
                """UPDATE books SET title=%s, author=%s, publisher=%s, publication_year=%s,
                   category=%s, listed_value=%s, total_quantity=%s,
                   available_quantity=%s WHERE book_code=%s""",
                (
                    data.get("title", current["title"]),
                    data.get("author", current["author"]),
                    data.get("publisher", current["publisher"]),
                    data.get("publication_year", current["publication_year"]),
                    data.get("category", current["category"]),
                    data.get("listed_value", current["listed_value"]),
                    new_total,
                    new_total - unavailable_count,
                    book_code,
                ),
            )
            db.commit()
            return True, "Cập nhật đầu sách thành công."
        except (ValueError, TypeError):
            db.rollback()
            return False, "Thông tin số lượng, năm xuất bản hoặc giá trị sách không hợp lệ."
        except Exception:
            db.rollback()
            raise
        finally:
            cursor.close()

    def deactivate(self, book_code: str) -> tuple[bool, str]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            db.start_transaction()
            cursor.execute("SELECT book_code FROM books WHERE book_code=%s FOR UPDATE", (book_code,))
            if not cursor.fetchone():
                db.rollback()
                return False, "Không tìm thấy đầu sách."
            cursor.execute(
                "SELECT COUNT(*) AS total FROM book_copies WHERE book_code=%s AND status='BORROWED'",
                (book_code,),
            )
            if int(cursor.fetchone()["total"]) > 0:
                db.rollback()
                return False, "Không thể ngừng kinh doanh khi vẫn còn bản sao đang được mượn."
            cursor.execute("UPDATE books SET is_active=FALSE WHERE book_code=%s", (book_code,))
            db.commit()
            return True, "Đã ngừng kinh doanh đầu sách."
        except Exception:
            db.rollback()
            raise
        finally:
            cursor.close()

    @staticmethod
    def _insert_copies(cursor, book_code: str, quantity: int) -> None:
        if quantity <= 0:
            return
        cursor.executemany(
            "INSERT INTO book_copies (copy_id, book_code, `condition`, status) VALUES (%s, %s, 'NORMAL', 'AVAILABLE')",
            [(f"CP-{uuid4().hex[:14].upper()}", book_code) for _ in range(quantity)],
        )
