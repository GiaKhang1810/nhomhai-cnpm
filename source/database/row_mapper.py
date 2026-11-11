from typing import Dict, Any, List
from source.domain.entities.book import Book
from source.domain.entities.user import User

def map_to_book(row: Dict[str, Any]) -> Book:
    return Book(
        book_code=row['book_code'],
        title=row['title'],
        author=row['author'],
        listed_value=float(row['listed_value']),
        publisher=row.get('publisher'),
        publication_year=row.get('publication_year'),
        category=row.get('category'),
        total_quantity=row.get('total_quantity', 0),
        available_quantity=row.get('available_quantity', 0)
    )

def map_to_user(row: Dict[str, Any]) -> User:
    return User(
        user_id=row['user_id'],
        username=row['username'],
        email=row['email'],
        password_hash=row['password_hash'],
        role=row['role'],
        account_status=row['account_status']
    )