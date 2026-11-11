from flask import Blueprint, render_template, session
from source.core.decorators import login_required, role_required

librarian_bp = Blueprint('librarian', __name__, url_prefix='/librarian')

@librarian_bp.route('/workspace', methods=['GET'])
@login_required
@role_required('LIBRARIAN')
def workspace():
    username = session.get('username', 'Thủ thư')
    
    stats = {
        'pending_requests': 12,
        'active_loans': 684,
        'due_today': 36,
        'overdue_books': 18
    }
    
    transactions = [
        {
            "loan_id": "#BR-2052", 
            "reader": "Nguyễn Minh Anh", 
            "book": "Đắc nhân tâm", 
            "borrow_date": "08/11/2026", 
            "due_date": "22/11/2026", 
            "status": "Đang duyệt", 
            "status_color": "bg-blue-50 text-blue-600",
            "action": "Duyệt"
        },
        {
            "loan_id": "#BR-2051", 
            "reader": "Trần Hoàng Nam", 
            "book": "Clean Code", 
            "borrow_date": "08/11/2026", 
            "due_date": "22/11/2026", 
            "status": "Đang duyệt", 
            "status_color": "bg-blue-50 text-blue-600",
            "action": "Duyệt"
        },
        {
            "loan_id": "#RT-1038", 
            "reader": "Lê Thu Hà", 
            "book": "Nhà giả kim", 
            "borrow_date": "08/11/2026", 
            "due_date": "-", 
            "status": "Trả sách", 
            "status_color": "bg-emerald-50 text-emerald-600",
            "action": "Chi tiết"
        },
        {
            "loan_id": "#BR-2048", 
            "reader": "Phạm Gia Bảo", 
            "book": "Tư duy nhanh và chậm", 
            "borrow_date": "07/11/2026", 
            "due_date": "14/11/2026", 
            "status": "Đang mượn", 
            "status_color": "bg-amber-50 text-amber-600",
            "action": "Chi tiết"
        }
    ]
    
    return render_template('librarian/workspace.html', 
                           username=username, 
                           stats=stats, 
                           transactions=transactions)