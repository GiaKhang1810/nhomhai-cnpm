from typing import Optional, List
from source.database.connection import get_db_connection
from source.domain.entities.reader import Reader

class ReaderRepository:
    def get_by_id(self, reader_id: str) -> Optional[Reader]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        query = "SELECT * FROM readers WHERE reader_id = %s"
        cursor.execute(query, (reader_id,))
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            return Reader(**row)
        return None

    def search_readers(self, keyword: str) -> List[Reader]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        search_pattern = f"%{keyword}%"
        query = """
            SELECT * FROM readers 
            WHERE reader_id LIKE %s OR full_name LIKE %s OR identity_number LIKE %s
        """
        cursor.execute(query, (search_pattern, search_pattern, search_pattern))
        rows = cursor.fetchall()
        cursor.close()
        return [Reader(**row) for row in rows]

    def create_reader_transaction(self, user_data: dict, reader_data: dict) -> bool:
        db = get_db_connection()
        cursor = db.cursor()
        try:
            user_query = """
                INSERT INTO users (username, email, password_hash, role, account_status)
                VALUES (%s, %s, %s, 'READER', 'ACTIVE')
            """
            cursor.execute(user_query, (
                user_data['username'], user_data['email'], user_data['password_hash']
            ))
            
            user_id = cursor.lastrowid
            
            reader_query = """
                INSERT INTO readers (
                    reader_id, user_id, full_name, dob, gender, 
                    identity_number, phone, card_issue_date, card_expiry_date, account_status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'ACTIVE')
            """
            cursor.execute(reader_query, (
                reader_data['reader_id'], user_id, reader_data['full_name'],
                reader_data.get('dob'), reader_data.get('gender'),
                reader_data['identity_number'], reader_data.get('phone'),
                reader_data['card_issue_date'], reader_data['card_expiry_date']
            ))
            
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Lỗi khi tạo độc giả: {e}")
            return False
        finally:
            cursor.close()