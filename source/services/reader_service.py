from uuid import uuid4
from datetime import date, timedelta
from typing import List, Tuple
from source.repositories.reader_repository import ReaderRepository
from source.core.security import hash_password

class ReaderService:
    def __init__(self):
        self.reader_repo = ReaderRepository()

    def search_readers(self, keyword: str):
        if not keyword:
            return []
        return self.reader_repo.search_readers(keyword)

    def create_new_reader(self, data: dict) -> Tuple[bool, str]:
        required_fields = ['full_name', 'identity_number', 'email', 'username', 'password']
        if not all(field in data for field in required_fields):
            return False, "Vui lòng điền đầy đủ các thông tin bắt buộc."

        hashed_password = hash_password(data['password'])

        user_data = {
            'username': data['username'],
            'email': data['email'],
            'password_hash': hashed_password
        }

        reader_id = f"RD-{str(uuid4().hex)[:6].upper()}"
        today = date.today()
        expiry_date = today.replace(year=today.year + 1)

        reader_data = {
            'reader_id': reader_id,
            'full_name': data['full_name'],
            'dob': data.get('dob'),
            'gender': data.get('gender'),
            'identity_number': data['identity_number'],
            'phone': data.get('phone'),
            'card_issue_date': today,
            'card_expiry_date': expiry_date
        }

        success = self.reader_repo.create_reader_transaction(user_data, reader_data)
        if success:
            return True, f"Tạo hồ sơ độc giả thành công. Mã độc giả: {reader_id}"
        return False, "Lỗi khi lưu dữ liệu. Có thể Username, Email hoặc CMND đã tồn tại."