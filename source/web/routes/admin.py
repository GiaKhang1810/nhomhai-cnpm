from flask import Blueprint, render_template, session, jsonify
from source.core.decorators import login_required, role_required
from source.database.connection import get_db_connection

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard', methods=['GET'])
@login_required
@role_required('ADMIN')
def dashboard():
    username = session.get('username', 'Quản trị viên')
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    total_titles = 0
    active_readers = 0
    active_loans = 0
    overdue_books = 0
    recent_transactions = []
    
    try:
        cursor.execute("SELECT COUNT(*) as cnt FROM books")
        res = cursor.fetchone()
        if res: total_titles = res['cnt']
        
        cursor.execute("SELECT COUNT(*) as cnt FROM readers")
        res = cursor.fetchone()
        if res: active_readers = res['cnt']
        
        cursor.execute("SELECT COUNT(*) as cnt FROM borrowing_details WHERE return_date IS NULL")
        res = cursor.fetchone()
        if res: active_loans = res['cnt']
        
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM borrowing_records br
            JOIN borrowing_details bd ON br.loan_id = bd.loan_id
            WHERE bd.return_date IS NULL AND br.due_date < CURDATE()
        """)
        res = cursor.fetchone()
        if res: overdue_books = res['cnt']
        
        cursor.execute("""
            SELECT br.loan_id, r.full_name as reader, b.title as book, 
                   br.borrow_date, br.due_date, br.status
            FROM borrowing_records br
            JOIN readers r ON br.reader_id = r.reader_id
            JOIN borrowing_details bd ON br.loan_id = bd.loan_id
            JOIN book_copies bc ON bd.copy_id = bc.copy_id
            JOIN books b ON bc.book_code = b.book_code
            ORDER BY br.borrow_date DESC
            LIMIT 5
        """)
        rows = cursor.fetchall()
        for row in rows:
            status_color = "bg-emerald-50 text-emerald-600"
            status_text = row['status']
            if status_text == 'OVERDUE':
                status_color = "bg-red-50 text-red-600"
                status_text = "Quá hạn"
            elif status_text == 'RETURNED':
                status_color = "bg-slate-100 text-slate-600"
                status_text = "Đã trả"
            else:
                status_text = "Đang mượn"
                
            recent_transactions.append({
                "loan_id": f"#BR-{row['loan_id']}",
                "reader": row['reader'],
                "book": row['book'],
                "date": row['borrow_date'].strftime('%d/%m/%Y') if row['borrow_date'] else '',
                "due_date": row['due_date'].strftime('%d/%m/%Y') if row['due_date'] else '',
                "status": status_text,
                "status_color": status_color
            })
    except Exception as e:
        print(f"Lỗi truy vấn Admin Dashboard: {e}")
    finally:
        cursor.close()

    metrics = {
        'total_titles': f"{total_titles:,}",
        'title_trend': "Hệ thống kho",
        'active_readers': f"{active_readers:,}",
        'reader_trend': "Thành viên",
        'active_loans': f"{active_loans}",
        'loan_note': "Bản đang cho mượn",
        'overdue_books': f"{overdue_books}",
        'overdue_note': "Cần xử lý ngay"
    }
    
    return render_template('admin/dashboard.html', 
                           username=username, 
                           metrics=metrics, 
                           recent_transactions=recent_transactions)

@admin_bp.route('/api/reports/dashboard', methods=['GET'])
@login_required
@role_required('ADMIN')
def api_dashboard_data():
    """API trả về JSON thống kê."""
    return jsonify({"success": True, "data": {}})