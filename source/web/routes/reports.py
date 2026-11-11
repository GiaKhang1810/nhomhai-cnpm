from flask import Blueprint, jsonify, render_template, session
from source.repositories.report_repository import ReportRepository
from source.core.decorators import login_required, role_required

reports_bp = Blueprint('reports', __name__, url_prefix='/admin/reports')
report_repo = ReportRepository()

@reports_bp.route('/dashboard', methods=['GET'])
@login_required
@role_required('ADMIN', 'LIBRARIAN')
def dashboard_data():
    metrics = report_repo.get_dashboard_metrics()
    return jsonify({"success": True, "data": metrics})

@reports_bp.route('/', methods=['GET'])
@login_required
@role_required('ADMIN')
def admin_dashboard_view():
    username = session.get('username', 'Quản trị viên')
    
    metrics_data = report_repo.get_dashboard_metrics()
    
    metrics = {
        'total_titles': f"{metrics_data.get('total_titles', 0):,}",
        'title_trend': "Cập nhật thời gian thực",
        'active_readers': f"{metrics_data.get('active_readers', 0):,}",
        'reader_trend': "Đang hoạt động",
        'active_loans': f"{metrics_data.get('currently_borrowed', 0)}",
        'loan_note': "Bản sao đang mượn",
        'overdue_books': f"{metrics_data.get('overdue_loans', 0)}",
        'overdue_note': "Cần xử lý ngay"
    }
    
    from source.database.connection import get_db_connection
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    recent_transactions = []
    try:
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
            if row['status'] == 'OVERDUE':
                status_color = "bg-red-50 text-red-600"
            elif row['status'] == 'RETURNED':
                status_color = "bg-slate-100 text-slate-600"
                
            recent_transactions.append({
                "loan_id": row['loan_id'],
                "reader": row['reader'],
                "book": row['book'],
                "date": row['borrow_date'].strftime('%d/%m/%Y') if row['borrow_date'] else '',
                "due_date": row['due_date'].strftime('%d/%m/%Y') if row['due_date'] else '',
                "status": row['status'],
                "status_color": status_color
            })
    except Exception as e:
        print(f"Lỗi lấy giao dịch gần đây: {e}")
    finally:
        cursor.close()

    return render_template('admin/dashboard.html', 
                           username=username, 
                           metrics=metrics, 
                           recent_transactions=recent_transactions)