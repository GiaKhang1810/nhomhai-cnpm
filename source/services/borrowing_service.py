from uuid import uuid4
from datetime import date, timedelta
from typing import List, Tuple
from source.domain.entities.borrowing import BorrowingRecord, BorrowingDetail
from source.repositories.borrowing_repository import BorrowingRepository
from source.repositories.reader_repository import ReaderRepository
from source.repositories.book_repository import BookRepository

class BorrowingService:
    def __init__(self):
        self.borrowing_repo = BorrowingRepository()
        self.reader_repo = ReaderRepository()
        self.book_repo = BookRepository()

    def process_borrowing(self, reader_id: str, copy_ids: List[str]) -> Tuple[bool, str]:
        if not copy_ids:
            return False, "Vui lòng chọn ít nhất 1 cuốn sách để mượn."

        reader = self.reader_repo.get_by_id(reader_id)
        if not reader:
            return False, "Không tìm thấy thông tin độc giả."
        
        today = date.today()
        if reader.card_expiry_date < today or reader.account_status != 'ACTIVE':
            return False, "Thẻ độc giả đã hết hạn hoặc bị khóa."

        current_borrowed = self.borrowing_repo.count_active_books_by_reader(reader_id)
        if current_borrowed + len(copy_ids) > 5:
            return False, f"Độc giả chỉ được mượn tối đa 5 cuốn. Đang mượn: {current_borrowed}."

        if self.borrowing_repo.has_overdue_books(reader_id):
            return False, "Độc giả đang có sách quá hạn chưa trả, không thể mượn thêm."

        loan_id = f"BR-{str(uuid4().hex)[:6].upper()}"
        due_date = today + timedelta(days=14)
        
        details = [BorrowingDetail(copy_id=cid) for cid in copy_ids]
        record = BorrowingRecord(
            loan_id=loan_id,
            reader_id=reader_id,
            borrow_date=today,
            due_date=due_date,
            details=details
        )

        success = self.borrowing_repo.create_loan_transaction(record)
        if success:
            return True, f"Tạo phiếu mượn thành công. Mã phiếu: {loan_id}"
        else:
            return False, "Đã có lỗi hệ thống xảy ra khi tạo phiếu mượn."