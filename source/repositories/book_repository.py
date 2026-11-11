from typing import List, Optional
from mysql.connector.cursor import MySQLCursorDict
from source.database.connection import get_db_connection
from source.domain.entities.book import Book
from source.database.row_mapper import map_to_book

class BookRepository:
    def get_by_code(self, book_code: str) -> Optional[Book]:
        db = get_db_connection()
        cursor: MySQLCursorDict = db.cursor(dictionary=True) 
        
        query = "SELECT * FROM books WHERE book_code = %s"
        cursor.execute(query, (book_code,))
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            return map_to_book(row)
        return None

    def search_books(self, keyword: str) -> List[Book]:
        db = get_db_connection()
        cursor: MySQLCursorDict = db.cursor(dictionary=True)
        
        search_pattern = f"%{keyword}%"
        query = """
            SELECT * FROM books 
            WHERE title LIKE %s OR author LIKE %s OR book_code LIKE %s
        """
        cursor.execute(query, (search_pattern, search_pattern, search_pattern))
        rows = cursor.fetchall()
        cursor.close()
        
        return [map_to_book(row) for row in rows]

    def create(self, book: Book) -> bool:
        db = get_db_connection()
        cursor = db.cursor()
        
        query = """
            INSERT INTO books 
            (book_code, title, author, publisher, publication_year, category, listed_value, total_quantity, available_quantity)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            book.book_code, book.title, book.author, book.publisher, 
            book.publication_year, book.category, book.listed_value,
            book.total_quantity, book.available_quantity
        )
        
        try:
            cursor.execute(query, values)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Lỗi khi thêm sách: {e}")
            return False
        finally:
            cursor.close()