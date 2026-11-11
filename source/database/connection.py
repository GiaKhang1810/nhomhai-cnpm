from mysql.connector import connect
from mysql.connector import Error
from mysql.connector.connection import MySQLConnection
from flask import g
from typing import Optional
from source.configs.settings import Config

def get_db_connection() -> MySQLConnection:
    if 'db' not in g:
        try:
            connection: MySQLConnection = connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                port=Config.DB_PORT
            )
            connection.autocommit = False 
            g.db = connection
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            raise e
    return g.db

def close_db_connection(e: Optional[Exception] = None) -> None:
    db: Optional[MySQLConnection] = g.pop('db', None)
    if db is not None:
        db.close()