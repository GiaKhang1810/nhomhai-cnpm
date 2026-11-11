from dataclasses import dataclass
from typing import Optional

@dataclass
class Book:
    book_code: str
    title: str
    author: str
    listed_value: float
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    category: Optional[str] = None
    total_quantity: int = 0
    available_quantity: int = 0