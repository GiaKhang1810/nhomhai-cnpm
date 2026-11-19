from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional, Any


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

    def update_book(self, **changes: Any) -> None:
        """Update mutable catalogue fields while enforcing domain constraints."""
        allowed = {
            "title", "author", "listed_value", "publisher", "publication_year",
            "category", "total_quantity", "available_quantity",
        }
        unknown = set(changes) - allowed
        if unknown:
            raise ValueError(f"Thuộc tính sách không được phép cập nhật: {', '.join(sorted(unknown))}.")

        candidate = {
            "title": self.title,
            "author": self.author,
            "listed_value": self.listed_value,
            "publisher": self.publisher,
            "publication_year": self.publication_year,
            "category": self.category,
            "total_quantity": self.total_quantity,
            "available_quantity": self.available_quantity,
        }
        candidate.update(changes)

        if not str(candidate["title"]).strip() or not str(candidate["author"]).strip():
            raise ValueError("Tên sách và tác giả không được để trống.")
        try:
            candidate["listed_value"] = Decimal(str(candidate["listed_value"]))
        except (InvalidOperation, TypeError, ValueError) as error:
            raise ValueError("Giá trị niêm yết không hợp lệ.") from error
        if not candidate["listed_value"].is_finite() or candidate["listed_value"] < 0:
            raise ValueError("Giá trị niêm yết không được âm.")
        if candidate["publication_year"] is not None:
            year = int(candidate["publication_year"])
            if not 1000 <= year <= 9999:
                raise ValueError("Năm xuất bản phải nằm trong khoảng 1000–9999.")
            candidate["publication_year"] = year
        total = int(candidate["total_quantity"])
        available = int(candidate["available_quantity"])
        if total < 0 or available < 0 or available > total:
            raise ValueError("Số lượng khả dụng phải nằm trong khoảng từ 0 đến tổng số lượng.")
        candidate["total_quantity"] = total
        candidate["available_quantity"] = available

        for field_name, value in candidate.items():
            setattr(self, field_name, value)

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True
