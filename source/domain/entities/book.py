from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(slots=True)
class Book:
    book_code: str
    title: str
    author: str
    listed_value: Decimal
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    category: Optional[str] = None
    total_quantity: int = 0
    available_quantity: int = 0
    is_active: bool = True
