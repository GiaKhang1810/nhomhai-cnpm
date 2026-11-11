from typing import Dict, Any
from source.database.connection import get_db_connection

class ReportRepository:
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        metrics = {}
        
        try:
            cursor.execute("SELECT COUNT(*) as total_titles FROM books")
            metrics['total_titles'] = cursor.fetchone()['total_titles']

            cursor.execute("SELECT COUNT(*) as active_readers FROM readers WHERE account_status = 'ACTIVE'")
            metrics['active_readers'] = cursor.fetchone()['active_readers']

            cursor.execute("SELECT COUNT(*) as currently_borrowed FROM book_copies WHERE status = 'BORROWED'")
            metrics['currently_borrowed'] = cursor.fetchone()['currently_borrowed']

            overdue_query = """
                SELECT COUNT(*) as overdue_loans 
                FROM borrowing_records br
                JOIN borrowing_details bd ON br.loan_id = bd.loan_id
                WHERE bd.return_date IS NULL AND br.due_date < CURDATE()
            """
            cursor.execute(overdue_query)
            metrics['overdue_loans'] = cursor.fetchone()['overdue_loans']
            
            return metrics
        finally:
            cursor.close()