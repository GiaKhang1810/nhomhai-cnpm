from typing import Dict, Any, Tuple

def validate_borrowing_request(data: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(data, dict):
        return False, "Dữ liệu không đúng định dạng."
        
    reader_id = data.get('reader_id')
    if not reader_id or not isinstance(reader_id, str):
        return False, "Mã độc giả không hợp lệ hoặc bị thiếu."
        
    copy_ids = data.get('copy_ids')
    if not copy_ids or not isinstance(copy_ids, list) or len(copy_ids) == 0:
        return False, "Danh sách mã bản sao sách không được để trống."
        
    if len(copy_ids) > 5:
        return False, "Không thể mượn quá 5 cuốn sách trong một lần yêu cầu."
        
    return True, "Hợp lệ"