from flask import Blueprint, render_template, session, redirect, url_for
from source.core.decorators import login_required, role_required
from source.database.connection import get_db_connection
from source.repositories.book_repository import BookRepository

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')
book_repo = BookRepository()

@profile_bp.route('/dashboard', methods=['GET'])
@login_required
@role_required('READER')
def dashboard():
    username = session.get('username', 'Độc giả')
    user_id = session.get('user_id')
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT reader_id FROM readers WHERE user_id = %s", (user_id,))
        reader_row = cursor.fetchone()
        
        borrowed_count = 0
        due_soon_count = 0
        
        if reader_row:
            reader_id = reader_row['reader_id']
            
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM borrowing_records br
                JOIN borrowing_details bd ON br.loan_id = bd.loan_id
                WHERE br.reader_id = %s AND bd.return_date IS NULL
            """, (reader_id,))
            res = cursor.fetchone()
            borrowed_count = res['count'] if res else 0
            
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM borrowing_records br
                JOIN borrowing_details bd ON br.loan_id = bd.loan_id
                WHERE br.reader_id = %s AND bd.return_date IS NULL 
                  AND br.due_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 3 DAY)
            """, (reader_id,))
            res_due = cursor.fetchone()
            due_soon_count = res_due['count'] if res_due else 0

        stats = {
            'borrowed_count': borrowed_count,
            'due_soon_count': due_soon_count,
            'points': 120 
        }
        
    except Exception as e:
        print(f"Lỗi truy vấn dashboard độc giả: {e}")
        stats = {'borrowed_count': 0, 'due_soon_count': 0, 'points': 0}
    finally:
        cursor.close()
    
    all_books = book_repo.search_books("")
    recommended_books = [
        {
            "title": b.title, 
            "author": b.author, 
            "available": b.available_quantity, 
            "color": "bg-blue-700"
        } for b in all_books[:4] 
    ]
    
    return render_template('reader/dashboard.html', 
                           username=username, 
                           stats=stats, 
                           recommended_books=recommended_books)