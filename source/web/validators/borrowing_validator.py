from typing import Any


def validate_borrowing_request(data: Any) -> tuple[bool, str]:
    if not isinstance(data, dict):
        return False, "Dữ liệu không đúng định dạng."
    reader_id = data.get("reader_id")
    if not isinstance(reader_id, str) or not reader_id.strip():
        return False, "Mã độc giả không hợp lệ hoặc bị thiếu."
    copy_ids = data.get("copy_ids")
    if not isinstance(copy_ids, list) or not copy_ids:
        return False, "Danh sách mã bản sao sách không được để trống."
    if len(copy_ids) > 5:
        return False, "Không thể mượn quá 5 cuốn sách trong một lần yêu cầu."
    if any(not isinstance(copy_id, str) or not copy_id.strip() for copy_id in copy_ids):
        return False, "Mã bản sao không hợp lệ."
    if len(copy_ids) != len(set(copy_ids)):
        return False, "Danh sách mã bản sao không được trùng lặp."
    return True, "Hợp lệ"
