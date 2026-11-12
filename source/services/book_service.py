from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from flask import current_app

from source.domain.entities.book import Book
from source.repositories.book_repository import BookRepository


class BookService:
    def __init__(self) -> None:
        self.book_repo = BookRepository()

    def search_books(self, keyword: str, *, include_inactive: bool = False) -> list[Book]:
        return self.book_repo.search_books(keyword, include_inactive=include_inactive)

    def get_book_details(self, book_code: str) -> Optional[Book]:
        return self.book_repo.get_by_code(book_code)

    def list_available_copies(self, book_code: str):
        return self.book_repo.list_available_copies(book_code)

    def add_new_book(self, data: dict[str, Any]) -> tuple[bool, str]:
        required = ("book_code", "title", "author")
        if any(not str(data.get(field, "")).strip() for field in required):
            return False, "Mã sách, tên sách và tác giả là bắt buộc."
        if len(str(data["book_code"]).strip()) > 20:
            return False, "Mã sách không được dài hơn 20 ký tự."
        try:
            quantity = int(data.get("total_quantity", 0))
            year = int(data["publication_year"]) if data.get("publication_year") not in (None, "") else None
            price = Decimal(str(data.get("listed_value", "0")))
            if quantity < 0 or price < 0 or not price.is_finite():
                return False, "Số lượng và giá trị sách không được âm hoặc không hợp lệ."
            if year is not None and not 1000 <= year <= 9999:
                return False, "Năm xuất bản không hợp lệ."
            if self.book_repo.get_by_code(str(data["book_code"]).strip()):
                return False, "Mã sách đã tồn tại trong hệ thống."
            book = Book(
                book_code=str(data["book_code"]).strip(),
                title=str(data["title"]).strip(),
                author=str(data["author"]).strip(),
                publisher=(str(data["publisher"]).strip() or None) if data.get("publisher") else None,
                publication_year=year,
                category=(str(data["category"]).strip() or None) if data.get("category") else None,
                listed_value=price,
                total_quantity=quantity,
                available_quantity=quantity,
            )
            self.book_repo.create(book)
            return True, "Thêm đầu sách và các bản sao thành công."
        except (ValueError, TypeError, InvalidOperation):
            return False, "Thông tin số lượng, năm xuất bản hoặc giá trị sách không hợp lệ."
        except Exception:
            current_app.logger.exception("Tạo đầu sách thất bại")
            return False, "Không thể lưu sách. Vui lòng kiểm tra mã sách và kết nối cơ sở dữ liệu."

    def update_book(self, book_code: str, data: dict[str, Any]) -> tuple[bool, str]:
        normalized = dict(data)
        for field in ("title", "author"):
            if field in normalized:
                normalized[field] = str(normalized[field]).strip()
                if not normalized[field]:
                    return False, f"{field} không được để trống."
        for field in ("publisher", "category"):
            if field in normalized:
                normalized[field] = str(normalized[field]).strip() or None
        try:
            if "total_quantity" in normalized:
                normalized["total_quantity"] = int(normalized["total_quantity"])
                if normalized["total_quantity"] < 0:
                    return False, "Số lượng sách không được âm."
            if "publication_year" in normalized:
                normalized["publication_year"] = int(normalized["publication_year"]) if normalized["publication_year"] else None
                if normalized["publication_year"] is not None and not 1000 <= normalized["publication_year"] <= 9999:
                    return False, "Năm xuất bản không hợp lệ."
            if "listed_value" in normalized:
                normalized["listed_value"] = Decimal(str(normalized["listed_value"]))
                if not normalized["listed_value"].is_finite() or normalized["listed_value"] < 0:
                    return False, "Giá trị sách không hợp lệ."
        except (ValueError, TypeError, InvalidOperation):
            return False, "Thông tin cập nhật không hợp lệ."
        return self.book_repo.update(book_code, normalized)

    def deactivate_book(self, book_code: str) -> tuple[bool, str]:
        return self.book_repo.deactivate(book_code)


    def activate_book(self, book_code: str) -> tuple[bool, str]:
        return self.book_repo.activate(book_code)

    def delete_book(self, book_code: str) -> tuple[bool, str]:
        return self.book_repo.delete(book_code)
