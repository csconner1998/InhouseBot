import psycopg2 

class DatabaseHandler:
    def __init__(self, host: str, db_name: str, user: str, password: str) -> None:
        self.connection = psycopg2.connect(
                            host=host,
                            database=db_name,
                            user=user,
                            password=password)
    
    def get_cursor(self):
        return self.connection.cursor()

    def complete_transaction(self, cursor):
        self.connection.commit()
        cursor.close()