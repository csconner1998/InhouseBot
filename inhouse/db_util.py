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
            cur.close()

    def addMatchReport(self,id):
        #if match reporter exists, skip
        cur = self.connection.cursor()
        cmd = "SELECT * FROM match_reporters WHERE player_id ='" + str(id) + "';"
        cur.execute(cmd)
        exists = bool(cur.rowcount)
        if exists:
            return
        #else make match reporter
        else:
            cmd = "INSERT INTO match_reporters(player_id) VALUES ('" +str(id) + "')"
            cur.execute(cmd)
            self.connection.commit()
            cur.close()
        
    def updateName(self, name, id):
        #if player exists, skip
        cur = self.connection.cursor()
        cmd = "UPDATE players SET name = '" + name + "' where id ='" + str(id) + "'"
        cur.execute(cmd)
        self.connection.commit()
        cur.close()
        #else make player

    def writePlayer(self, WinLoss, playerID):
        cur = self.connection.cursor()
        cmd = "SELECT win, loss,sp FROM players WHERE id ='" + str(playerID) + "'"
        cur.execute(cmd)
        value = cur.fetchone()
        winNum = int(value[0])
        losNum = int(value[1])
        spNum = int(value[2])
        if str.lower(WinLoss) == "w":
            winNum += 1
            spNum += 15
        else:
            losNum += 1
            spNum -= 12
            if spNum < 0:
                spNum = 0
        ratioStr = int(100 * (winNum / (winNum + losNum)))
        cur = self.connection.cursor()
        # Join new_data with file_data inside emp_details'
        cmd = "UPDATE players SET win = '"+str(winNum)+"', loss = '"+str(losNum)+"', sp = '"+str(spNum)+"', ratio = '"+str(ratioStr)+"' where id ='" + str(playerID) + "';"
        cur.execute(cmd)
        self.connection.commit()
        cur.close
        # Sets file's current position at offset.
        # convert back to json.
    
    def getCursor(self):
        return self.connection.cursor()

    def completeTransaction(self, cursor):
        self.connection.commit()
        cursor.close()