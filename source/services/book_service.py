from typing import List, Tuple, Optional
from source.domain.entities.book import Book
from source.repositories.book_repository import BookRepository

class BookService:
    def __init__(self):
        self.book_repo = BookRepository()

    def search_books(self, keyword: str) -> List[Book]:
        if not keyword:
            return []
        return self.book_repo.search_books(keyword)

    def get_book_details(self, book_code: str) -> Optional[Book]:
        return self.book_repo.get_by_code(book_code)

    def add_new_book(self, book_data: dict) -> Tuple[bool, str]:
        existing_book = self.book_repo.get_by_code(book_data.get('book_code'))
        if existing_book:
            return False, "Mã sách đã tồn tại trong hệ thống."

        try:
            total_qty = int(book_data.get('total_quantity', 0))
            new_book = Book(
                book_code=book_data['book_code'],
                title=book_data['title'],
                author=book_data['author'],
                publisher=book_data.get('publisher'),
                publication_year=int(book_data['publication_year']) if book_data.get('publication_year') else None,
                category=book_data.get('category'),
                listed_value=float(book_data.get('listed_value', 0.0)),
                total_quantity=total_qty,
                available_quantity=total_qty 
            )
            
            success = self.book_repo.create(new_book)
            if success:
                return True, "Thêm đầu sách thành công."
            return False, "Lỗi khi lưu sách vào cơ sở dữ liệu."
        except Exception as e:
            return False, f"Lỗi dữ liệu: {e}"