from flask import Blueprint, request, jsonify
from source.services.book_service import BookService
from source.core.decorators import login_required, role_required
from time import time

books_bp = Blueprint('books', __name__, url_prefix='/api/books')
book_service = BookService()

@books_bp.route('/search', methods=['GET'])
@login_required
def search():
    start_time = time()
    keyword = request.args.get('q', '').strip()
    
    if not keyword:
        return jsonify({"success": False, "message": "Vui lòng nhập từ khóa tìm kiếm."}), 400
        
    books = book_service.search_books(keyword)
    
    books_data = [
        {
            "book_code": b.book_code,
            "title": b.title,
            "author": b.author,
            "category": b.category,
            "available_quantity": b.available_quantity
        } for b in books
    ]
    
    process_time = time() - start_time
    if process_time > 2.0:
        print(f"Warning: Search took {process_time} seconds (limit is 2s).")

    return jsonify({
        "success": True,
        "data": books_data,
        "count": len(books_data),
        "process_time_seconds": round(process_time, 4)
    })

@books_bp.route('/', methods=['POST'])
@login_required
@role_required('LIBRARIAN', 'ADMIN') 
def add_book():
    """API thêm sách mới."""
    data = request.json
    if not data:
        return jsonify({"success": False, "message": "Dữ liệu không hợp lệ."}), 400

    success, message = book_service.add_new_book(data)
    
    status_code = 201 if success else 400
    return jsonify({"success": success, "message": message}), status_code

@books_bp.route('/<book_code>', methods=['GET'])
@login_required
def get_book(book_code):
    book = book_service.get_book_details(book_code)
    if not book:
        return jsonify({"success": False, "message": "Không tìm thấy sách."}), 404
        
    return jsonify({
        "success": True,
        "data": {
            "book_code": book.book_code,
            "title": book.title,
            "author": book.author,
            "publisher": book.publisher,
            "publication_year": book.publication_year,
            "category": book.category,
            "listed_value": book.listed_value,
            "total_quantity": book.total_quantity,
            "available_quantity": book.available_quantity
        }
    })