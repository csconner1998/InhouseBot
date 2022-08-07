import psycopg2 

class DatabaseHandler:
    def __init__(self, host: str, db_name: str, user: str, password: str) -> None:
        self.connection = psycopg2.connect(
                            host=host,
                            database=db_name,
                            user=user,
                            password=password)

    def makePlayer(self, name, id):
        #if player exists, skip
        cur = self.connection.cursor()
        cmd = "SELECT * FROM players WHERE id ='" + str(id) + "';"
        cur.execute(cmd)
        exists = bool(cur.rowcount)
        if exists:
            # cmd = "UPDATE players SET name = '" + name + "' where id ='" + str(id) + "'"
            # cur.execute(cmd)
            # conn.commit()
            return
        #else make player
        else:
            cmd = "INSERT INTO players(id, name, win, loss, ratio, sp) VALUES ('" + str(id) + "', '" + name + "', '0', '0', '0', '500')"
            cur.execute(cmd)
            self.connection.commit()

    def updateName(self, name, id):
        #if player exists, skip
        cur = self.connection.cursor()
        cmd = "UPDATE players SET name = '" + name + "' where id ='" + str(id) + "'"
        cur.execute(cmd)
        self.connection.commit()
        cur.close()
        #else make player
    
    def get_cursor(self):
        return self.connection.cursor()

    def complete_transaction(self, cursor):
        self.connection.commit()
        cursor.close()