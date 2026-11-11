from uuid import uuid4
from typing import Tuple
from source.database.connection import get_db_connection
from source.core.security import hash_password

class AccountService:
    def create_staff_account(self, data: dict) -> Tuple[bool, str]:
        db = get_db_connection()
        cursor = db.cursor()
        
        try:
            hashed_password = hash_password(data['password'])
            role = data.get('role', 'LIBRARIAN')
            
            user_query = """
                INSERT INTO users (username, email, password_hash, role, account_status)
                VALUES (%s, %s, %s, %s, 'ACTIVE')
            """
            cursor.execute(user_query, (data['username'], data['email'], hashed_password, role))
            user_id = cursor.lastrowid
            
            staff_id = f"STF-{str(uuid4().hex)[:6].upper()}"
            staff_query = "INSERT INTO librarians (staff_id, user_id, full_name, phone) VALUES (%s, %s, %s, %s)"
            cursor.execute(staff_query, (staff_id, user_id, data['full_name'], data.get('phone')))
            
            db.commit()
            return True, f"Tạo tài khoản nhân viên thành công. Mã NV: {staff_id}"
        except Exception as e:
            db.rollback()
            return False, "Lỗi tạo tài khoản. Username hoặc Email có thể đã tồn tại."
        finally:
            cursor.close()