from typing import Optional, Dict, Any
from source.database.connection import get_db_connection
from source.core.security import verify_password
from source.domain.entities.user import User
from source.database.row_mapper import map_to_user

class AuthService:
    def authenticate(self, username_or_email: str, password: str) -> Optional[User]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = "SELECT * FROM users WHERE username = %s OR email = %s"
        cursor.execute(query, (username_or_email, username_or_email))
        row = cursor.fetchone()
        cursor.close()
        
        if not row:
            return None
            
        user = map_to_user(row)
        print(user)
        
        if user.account_status != 'ACTIVE':
            return None
            
        if verify_password(password, user.password_hash):
            return user
            
        return None