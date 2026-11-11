from typing import List
from source.database.connection import get_db_connection
from source.domain.entities.borrowing import BorrowingRecord

class BorrowingRepository:
    def count_active_books_by_reader(self, reader_id: str) -> int:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        query = """
            SELECT COUNT(bd.copy_id) as total
            FROM borrowing_records br
            JOIN borrowing_details bd ON br.loan_id = bd.loan_id
            WHERE br.reader_id = %s AND bd.return_date IS NULL
        """
        cursor.execute(query, (reader_id,))
        result = cursor.fetchone()
        cursor.close()
        return result['total'] if result else 0

    def has_overdue_books(self, reader_id: str) -> bool:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        query = """
            SELECT COUNT(br.loan_id) as overdue_count
            FROM borrowing_records br
            JOIN borrowing_details bd ON br.loan_id = bd.loan_id
            WHERE br.reader_id = %s 
              AND bd.return_date IS NULL 
              AND br.due_date < CURDATE()
        """
        cursor.execute(query, (reader_id,))
        result = cursor.fetchone()
        cursor.close()
        return (result['overdue_count'] > 0) if result else False

    def create_loan_transaction(self, record: BorrowingRecord) -> bool:
        db = get_db_connection()
        cursor = db.cursor()
        try:
            query_record = """
                INSERT INTO borrowing_records (loan_id, reader_id, borrow_date, due_date, status)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query_record, (
                record.loan_id, record.reader_id, record.borrow_date, 
                record.due_date, record.status
            ))

            query_detail = """
                INSERT INTO borrowing_details (loan_id, copy_id)
                VALUES (%s, %s)
            """
            query_update_copy = """
                UPDATE book_copies SET status = 'BORROWED' WHERE copy_id = %s
            """
            query_update_book = """
                UPDATE books SET available_quantity = available_quantity - 1 
                WHERE book_code = (SELECT book_code FROM book_copies WHERE copy_id = %s)
            """

            for detail in record.details:
                cursor.execute(query_detail, (record.loan_id, detail.copy_id))
                cursor.execute(query_update_copy, (detail.copy_id,))
                cursor.execute(query_update_book, (detail.copy_id,))

            db.commit() 
            return True
        except Exception as e:
            db.rollback()
            print(f"Transaction Failed: {e}")
            return False
        finally:
            cursor.close()