from typing import Any, Mapping
from source.domain.entities.book import Book
from source.domain.entities.user import User


def map_to_book(row: Mapping[str, Any]) -> Book:
    return Book(
        book_code=row["book_code"],
        title=row["title"],
        author=row["author"],
        listed_value=row["listed_value"],
        publisher=row.get("publisher"),
        publication_year=row.get("publication_year"),
        category=row.get("category"),
        total_quantity=int(row.get("total_quantity", 0)),
        available_quantity=int(row.get("available_quantity", 0)),
        is_active=bool(row.get("is_active", True)),
    )


def map_to_user(row: Mapping[str, Any]) -> User:
    return User(
        user_id=row["user_id"],
        username=row["username"],
        email=row["email"],
        password_hash=row["password_hash"],
        role=row["role"],
        account_status=row["account_status"],
    )
