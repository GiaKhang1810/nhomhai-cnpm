from typing import List, Dict, Any, Optional
from datetime import date
from source.database.connection import get_db_connection

class ReturnRepository:
    def get_loan_info(self, loan_id: str) -> Optional[Dict[str, Any]]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        query = "SELECT loan_id, reader_id, due_date, status FROM borrowing_records WHERE loan_id = %s"
        cursor.execute(query, (loan_id,))
        row = cursor.fetchone()
        cursor.close()
        return row

    def get_copy_info(self, copy_id: str) -> Optional[Dict[str, Any]]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        query = """
            SELECT bc.copy_id, bc.book_code, b.listed_value 
            FROM book_copies bc
            JOIN books b ON bc.book_code = b.book_code
            WHERE bc.copy_id = %s
        """
        cursor.execute(query, (copy_id,))
        row = cursor.fetchone()
        cursor.close()
        return row

    def process_return_transaction(self, loan_id: str, return_date: date, items: List[Dict[str, Any]]) -> bool:
        db = get_db_connection()
        cursor = db.cursor()
        
        try:
            update_detail_query = """
                UPDATE borrowing_details 
                SET return_date = %s, overdue_fine = %s, compensation = %s
                WHERE loan_id = %s AND copy_id = %s
            """
            update_copy_query = "UPDATE book_copies SET status = %s, `condition` = %s WHERE copy_id = %s"
            update_book_qty_query = "UPDATE books SET available_quantity = available_quantity + 1 WHERE book_code = %s"

            for item in items:
                cursor.execute(update_detail_query, (
                    return_date, item['overdue_fine'], item['compensation'], loan_id, item['copy_id']
                ))
                
                cursor.execute(update_copy_query, (item['copy_status'], item['condition'], item['copy_id']))
                
                if item['copy_status'] == 'AVAILABLE':
                    cursor.execute(update_book_qty_query, (item['book_code'],))

            check_all_returned_query = """
                SELECT COUNT(*) as unreturned 
                FROM borrowing_details 
                WHERE loan_id = %s AND return_date IS NULL
            """
            cursor.execute(check_all_returned_query, (loan_id,))
            unreturned_count = cursor.fetchone()[0]
            
            if unreturned_count == 0:
                cursor.execute("UPDATE borrowing_records SET status = 'RETURNED' WHERE loan_id = %s", (loan_id,))

            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Lỗi khi trả sách: {e}")
            return False
        finally:
            cursor.close()