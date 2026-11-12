from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from source.database.connection import get_db_connection


class ReportRepository:
    def get_dashboard_metrics(self) -> dict[str, int]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute("SELECT COUNT(*) AS total_titles, COALESCE(SUM(total_quantity),0) AS total_copies FROM books WHERE is_active=TRUE")
            books = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) AS active_readers FROM readers WHERE account_status='ACTIVE' AND card_expiry_date >= CURDATE()")
            readers = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) AS currently_borrowed FROM book_copies WHERE status='BORROWED'")
            borrowed = cursor.fetchone()
            cursor.execute("SELECT COALESCE(SUM(available_quantity),0) AS available_copies FROM books WHERE is_active=TRUE")
            available = cursor.fetchone()
            cursor.execute(
                """SELECT COUNT(*) AS overdue_loans FROM borrowing_details bd
                   JOIN borrowing_records br ON br.loan_id=bd.loan_id
                   WHERE bd.return_date IS NULL AND br.due_date < CURDATE()"""
            )
            overdue = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) AS new_readers FROM readers WHERE card_issue_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)")
            new_readers = cursor.fetchone()
            return {
                "total_titles": int(books["total_titles"]),
                "total_copies": int(books["total_copies"]),
                "active_readers": int(readers["active_readers"]),
                "currently_borrowed": int(borrowed["currently_borrowed"]),
                "available_copies": int(available["available_copies"]),
                "overdue_loans": int(overdue["overdue_loans"]),
                "new_readers_30_days": int(new_readers["new_readers"]),
            }
        finally:
            cursor.close()

    def get_activity_stats(self, days: int = 7) -> list[dict[str, Any]]:
        days = max(1, min(int(days), 90))
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT activity_date,
                          SUM(borrowed_count) AS borrowed_count,
                          SUM(returned_count) AS returned_count
                   FROM (
                       SELECT br.borrow_date AS activity_date, COUNT(*) AS borrowed_count, 0 AS returned_count
                       FROM borrowing_records br
                       JOIN borrowing_details bd ON bd.loan_id=br.loan_id
                       WHERE br.borrow_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                       GROUP BY br.borrow_date
                       UNION ALL
                       SELECT return_date AS activity_date, 0 AS borrowed_count, COUNT(*) AS returned_count
                       FROM borrowing_details WHERE return_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                       GROUP BY return_date
                   ) AS activity
                   GROUP BY activity_date ORDER BY activity_date""",
                (days, days),
            )
            rows = {row["activity_date"]: row for row in cursor.fetchall()}
            today = date.today()
            return [
                {
                    "date": (today - timedelta(days=offset)).isoformat(),
                    "borrowed": int(rows.get(today - timedelta(days=offset), {}).get("borrowed_count", 0) or 0),
                    "returned": int(rows.get(today - timedelta(days=offset), {}).get("returned_count", 0) or 0),
                }
                for offset in range(days - 1, -1, -1)
            ]
        finally:
            cursor.close()

    def get_category_distribution(self) -> list[dict[str, Any]]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT COALESCE(category, 'Chưa phân loại') AS category, SUM(total_quantity) AS copies FROM books WHERE is_active=TRUE GROUP BY category ORDER BY copies DESC"
            )
            return [{"category": row["category"], "copies": int(row["copies"] or 0)} for row in cursor.fetchall()]
        finally:
            cursor.close()

    def get_recent_transactions(self, limit: int = 10) -> list[dict[str, Any]]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT br.loan_id, r.full_name AS reader, b.title AS book,
                          br.borrow_date, br.due_date,
                          CASE WHEN SUM(bd.return_date IS NULL)=0 THEN 'RETURNED'
                               WHEN br.due_date < CURDATE() THEN 'OVERDUE'
                               ELSE 'BORROWED' END AS status
                   FROM borrowing_records br
                   JOIN readers r ON r.reader_id=br.reader_id
                   JOIN borrowing_details bd ON bd.loan_id=br.loan_id
                   JOIN book_copies bc ON bc.copy_id=bd.copy_id
                   JOIN books b ON b.book_code=bc.book_code
                   GROUP BY br.loan_id, r.full_name, b.title, br.borrow_date, br.due_date
                   ORDER BY br.borrow_date DESC LIMIT %s""",
                (max(1, min(int(limit), 100)),),
            )
            return cursor.fetchall()
        finally:
            cursor.close()
