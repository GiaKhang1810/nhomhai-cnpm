from __future__ import annotations

import re
from calendar import monthrange
from datetime import date
from typing import Any
from uuid import uuid4

from source.core.security import hash_password
from source.repositories.reader_repository import ReaderRepository


class ReaderService:
    def __init__(self) -> None:
        self.reader_repo = ReaderRepository()

    def search_readers(self, keyword: str):
        return self.reader_repo.search_readers(keyword) if keyword.strip() else []

    def create_new_reader(self, data: dict[str, Any]) -> tuple[bool, str]:
        required = ("full_name", "identity_number", "email", "username", "password")
        if any(not str(data.get(field, "")).strip() for field in required):
            return False, "Vui lòng điền đầy đủ các thông tin bắt buộc."
        username = str(data["username"]).strip()
        email = str(data["email"]).strip().lower()
        password = str(data["password"])
        if len(password) < 8:
            return False, "Mật khẩu phải có ít nhất 8 ký tự."
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            return False, "Địa chỉ email không hợp lệ."
        try:
            today = date.today()
            expiry_year = today.year + 1
            expiry = today.replace(year=expiry_year, day=min(today.day, monthrange(expiry_year, today.month)[1]))
            dob = date.fromisoformat(data["dob"]) if data.get("dob") else None
            if dob and dob > today:
                return False, "Ngày sinh không được ở tương lai."
            gender = str(data.get("gender") or "").upper() or None
            if gender and gender not in {"MALE", "FEMALE", "OTHER"}:
                return False, "Giới tính không hợp lệ."
            reader_data = {
                "reader_id": f"RD-{uuid4().hex[:10].upper()}",
                "full_name": str(data["full_name"]).strip(),
                "dob": dob,
                "gender": gender,
                "identity_number": str(data["identity_number"]).strip(),
                "phone": str(data.get("phone", "")).strip() or None,
                "card_issue_date": today,
                "card_expiry_date": expiry,
            }
            user_data = {
                "username": username,
                "email": email,
                "password_hash": hash_password(password),
            }
            self.reader_repo.create_reader_transaction(user_data, reader_data)
            return True, f"Tạo hồ sơ độc giả thành công. Mã độc giả: {reader_data['reader_id']}"
        except ValueError:
            return False, "Ngày sinh không hợp lệ."
        except Exception:
            return False, "Không thể tạo độc giả. Username, email hoặc số giấy tờ có thể đã tồn tại."

    def update_reader(self, reader_id: str, data: dict[str, Any]) -> tuple[bool, str]:
        normalized = dict(data)
        if "full_name" in normalized:
            normalized["full_name"] = str(normalized["full_name"]).strip()
            if not normalized["full_name"]:
                return False, "Họ tên không được để trống."
        if "identity_number" in normalized:
            normalized["identity_number"] = str(normalized["identity_number"]).strip()
            if not normalized["identity_number"]:
                return False, "Số giấy tờ không được để trống."
        if "phone" in normalized:
            normalized["phone"] = str(normalized["phone"]).strip() or None
        if "gender" in normalized:
            gender = str(normalized["gender"] or "").upper() or None
            if gender and gender not in {"MALE", "FEMALE", "OTHER"}:
                return False, "Giới tính không hợp lệ."
            normalized["gender"] = gender
        try:
            today = date.today()
            if "dob" in normalized:
                normalized["dob"] = date.fromisoformat(normalized["dob"]) if normalized["dob"] else None
                if normalized["dob"] and normalized["dob"] > today:
                    return False, "Ngày sinh không được ở tương lai."
            if "card_expiry_date" in normalized:
                if not normalized["card_expiry_date"]:
                    return False, "Ngày hết hạn thẻ không được để trống."
                normalized["card_expiry_date"] = date.fromisoformat(normalized["card_expiry_date"])
                reader = self.reader_repo.get_by_id(reader_id)
                if not reader:
                    return False, "Không tìm thấy độc giả."
                if normalized["card_expiry_date"] < reader.card_issue_date:
                    return False, "Ngày hết hạn thẻ phải sau ngày cấp thẻ."
            return self.reader_repo.update_reader(reader_id, normalized)
        except ValueError:
            return False, "Ngày tháng không hợp lệ."
        except Exception:
            return False, "Không thể cập nhật hồ sơ. Số giấy tờ có thể đã được sử dụng."

    def deactivate_reader(self, reader_id: str) -> tuple[bool, str]:
        return self.reader_repo.deactivate_reader(reader_id)
