import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="flask_user",
        password="pass",
        database="expense_tracker_db"
    )
