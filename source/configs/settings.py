from os import environ
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY: str = environ.get("SECRET_KEY")

    DB_HOST: str = environ.get("DB_HOST")
    DB_USER: str = environ.get("DB_USER")
    DB_PASSWORD: str = environ.get("DB_PASSWORD")
    DB_NAME: str = environ.get("DB_NAME")
    DB_PORT: int = int(environ.get("DB_PORT", "3306"))
