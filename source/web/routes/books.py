from flask import Blueprint, jsonify, request, session

from source.core.decorators import login_required, role_required
from source.services.book_service import BookService

books_bp = Blueprint("books", __name__, url_prefix="/api/books")
book_service = BookService()


def _serialize_book(book):
    return {
        "book_code": book.book_code,
        "title": book.title,
        "author": book.author,
        "publisher": book.publisher,
        "publication_year": book.publication_year,
        "category": book.category,
        "listed_value": str(book.listed_value),
        "total_quantity": book.total_quantity,
        "available_quantity": book.available_quantity,
        "is_active": book.is_active,
    }


@books_bp.get("/search")
@login_required
def search():
    keyword = request.args.get("q", "").strip()
    if not keyword:
        return jsonify({"success": False, "message": "Vui lòng nhập từ khóa tìm kiếm."}), 400
    books = book_service.search_books(keyword)
    response = jsonify({"success": True, "data": [_serialize_book(book) for book in books], "count": len(books)})
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


@books_bp.get("/")
@login_required
def collection():
    keyword = request.args.get("q", "").strip()
    include_inactive = request.args.get("include_inactive") == "true" and session.get("role") in {"LIBRARIAN", "ADMIN"}
    books = book_service.search_books(keyword, include_inactive=include_inactive)
    response = jsonify({"success": True, "data": [_serialize_book(book) for book in books], "count": len(books)})
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


@books_bp.post("/")
@login_required
@role_required("LIBRARIAN", "ADMIN")
def create_book():
    data = request.get_json(silent=True) or {}
    success, message = book_service.add_new_book(data)
    response = jsonify({"success": success, "message": message})
    response.status_code = 201 if success else 400
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


@books_bp.get("/<string:book_code>")
@login_required
def get_book(book_code: str):
    book = book_service.get_book_details(book_code)
    if not book or not book.is_active:
        return jsonify({"success": False, "message": "Không tìm thấy sách."}), 404
    return jsonify({"success": True, "data": _serialize_book(book)})


@books_bp.put("/<string:book_code>")
@login_required
@role_required("LIBRARIAN", "ADMIN")
def update_book(book_code: str):
    data = request.get_json(silent=True) or {}
    success, message = book_service.update_book(book_code, data)
    response = jsonify({"success": success, "message": message})
    response.status_code = 200 if success else 400
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


@books_bp.patch("/<string:book_code>/deactivate")
@login_required
@role_required("LIBRARIAN", "ADMIN")
def deactivate_book(book_code: str):
    success, message = book_service.deactivate_book(book_code)
    response = jsonify({"success": success, "message": message})
    response.status_code = 200 if success else 400
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


@books_bp.patch("/<string:book_code>/activate")
@login_required
@role_required("LIBRARIAN", "ADMIN")
def activate_book(book_code: str):
    success, message = book_service.activate_book(book_code)
    response = jsonify({"success": success, "message": message})
    response.status_code = 200 if success else 400
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


@books_bp.delete("/<string:book_code>")
@login_required
@role_required("LIBRARIAN", "ADMIN")
def delete_book(book_code: str):
    success, message = book_service.delete_book(book_code)
    response = jsonify({"success": success, "message": message})
    response.status_code = 200 if success else 400
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response



@books_bp.get("/<string:book_code>/copies")
@login_required
@role_required("LIBRARIAN", "ADMIN")
def list_available_copies(book_code: str):
    book = book_service.get_book_details(book_code)
    if not book or not book.is_active:
        return jsonify({"success": False, "message": "Không tìm thấy sách."}), 404
    return jsonify({"success": True, "data": book_service.list_available_copies(book_code)})
