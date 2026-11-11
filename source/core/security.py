from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return check_password_hash(hashed_password, plain_password)
    except (ValueError, TypeError):
        return False
