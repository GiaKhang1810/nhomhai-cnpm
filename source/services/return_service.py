from datetime import date
from typing import List, Tuple
from dataclasses import dataclass
from source.repositories.return_repository import ReturnRepository

@dataclass
class ReturnItemRequest:
    copy_id: str
    condition: str

class ReturnService:
    def __init__(self):
        self.return_repo = ReturnRepository()

    def process_returns(self, loan_id: str, returned_items: List[ReturnItemRequest]) -> Tuple[bool, str, float]:
        if not returned_items:
            return False, "Không có sách nào được chọn để trả.", 0.0

        loan = self.return_repo.get_loan_info(loan_id)
        if not loan:
            return False, "Không tìm thấy thông tin phiếu mượn.", 0.0

        today = date.today()
        due_date = loan['due_date']
        
        overdue_days = (today - due_date).days if today > due_date else 0
        
        processed_items = []
        total_charge = 0.0

        for req in returned_items:
            copy_info = self.return_repo.get_copy_info(req.copy_id)
            if not copy_info:
                return False, f"Không tìm thấy dữ liệu cho mã sách {req.copy_id}.", 0.0

            overdue_fine = overdue_days * 5000.0 if overdue_days > 0 else 0.0
            
            compensation = 0.0
            copy_status = 'AVAILABLE'
            
            if req.condition in ['DAMAGED', 'LOST']:
                compensation = copy_info['listed_value']
                copy_status = req.condition

            total_charge += (overdue_fine + compensation)

            processed_items.append({
                'copy_id': req.copy_id,
                'book_code': copy_info['book_code'],
                'condition': req.condition,
                'copy_status': copy_status,
                'overdue_fine': overdue_fine,
                'compensation': compensation
            })

        success = self.return_repo.process_return_transaction(loan_id, today, processed_items)
        
        if success:
            msg = f"Trả sách thành công."
            if total_charge > 0:
                msg += f" Tổng phí phát sinh: {total_charge:,.0f} VND."
            return True, msg, total_charge
        else:
            return False, "Lỗi hệ thống khi ghi nhận trả sách.", 0.0