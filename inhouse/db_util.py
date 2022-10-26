import psycopg2 
import discord

class DatabaseHandler:
    def __init__(self, host: str, db_name: str, user: str, password: str) -> None:
        self.connection = psycopg2.connect(
                            host=host,
                            database=db_name,
                            user=user,
                            password=password)
    
    def get_cursor(self):
        return self.connection.cursor()

    def complete_transaction(self, cursor, cmds: list):
        '''
        attempts to complete the given command(s) using the given cursor, rolling back on a failure to prevent sql crashers

        This should be used on any CREATE/UPDATE/DELTE operations. It should be unnecessary for any SELECT operations
        '''

        try:
            for cmd in cmds:
                cursor.execute(cmd)
        except psycopg2.IntegrityError:
            cursor.rollback()
        else:
            self.connection.commit()
        cursor.close()

    async def get_names(self):
        cur = self.get_cursor()
        cmd = "SELECT league_name, discord_id, last_lp, puuid, sum_id FROM soloqueue_leaderboard;"
        cur.execute(cmd)
        retList = cur.fetchall()
        return retList

    async def get_soloq_entry_by_name(self, name: str):
        cur = self.get_cursor()
        cmd = f"SELECT discord_id FROM soloqueue_leaderboard where league_name = '{name}'"
        cur.execute(cmd)
        id_entry = cur.fetchone()
        return id_entry[0]

    async def get_missing_names(self):
        cur = self.get_cursor()
        cmd = "SELECT discord_id, league_name FROM soloqueue_leaderboard where puuid is NULL;"
        cur.execute(cmd)
        retList = cur.fetchall()
        return retList

    async def delete_missing_puuid(self):
        cur = self.get_cursor()
        cmd = "DELETE FROM soloqueue_leaderboard where puuid is NULL;"
        cur.execute(cmd)
        retList = cur.fetchall()
        return retList

    async def set_show_rank(self,id,name,opt,sumID=None,puuid=None):
        cur = self.get_cursor()
        cmd = f"SELECT discord_id FROM soloqueue_leaderboard where discord_id = {id};"
        cur.execute(cmd)
        exists = cur.fetchone()
        if exists and opt:
            return
        if opt:
            cmd = f"INSERT into soloqueue_leaderboard(discord_id,league_name,puuid,sum_id) VALUES ('{id}', '{name}', '{puuid}','{sumID}')"
            self.complete_transaction(cur, [cmd])
        else:
            cmd = f"DELETE FROM soloqueue_leaderboard WHERE discord_id = '{id}'"
            self.complete_transaction(cur, [cmd])

    
    async def update_sum_ids(self,disc_id, sum_id, puuid):
        cur = self.get_cursor()
        cmd = f"UPDATE soloqueue_leaderboard SET sum_id = '{sum_id}', puuid = '{puuid}'  WHERE discord_id = '{disc_id}'"
        cur.execute(cmd)
        self.complete_transaction(cur)
        
    async def set_week_lp(self,id,lp):
        cur = self.get_cursor()
        cmd = f"UPDATE soloqueue_leaderboard SET last_lp = '{lp}' WHERE discord_id = '{id}'"
        self.complete_transaction(cur, [cmd])

    async def get_match_history(self, ctx, count):
        cur = self.get_cursor()
        cmd = f"SELECT match_id, name, blue, winner FROM matches_players INNER JOIN players ON matches_players.player_id = players.id inner join matches on matches_players.match_id = matches.matchid ORDER BY matches.matchid DESC, blue ASC limit {count*10};"
        cur.execute(cmd)
        retList = cur.fetchall()
        totalStr = "```Match History``\n`"
        gameIDstr = ""
        blueString = ""
        redString = ""
        print(retList)
        for i in range(len(retList)):
            if i % 10 == 0:
                if i != 0:
                    totalStr += f"{gameIDstr}\n{blueString}\n{redString}\n\n"
                    print(totalStr)
                gameIDstr= f"**__Game ID: {str(retList[i][0])}__**"
                redString = "**Red** | "
                blueString = "**Blue** | "

            #Is blue
            if retList[i][2]:
                blueString += retList[i][1] + " | "
                if i % 5 == 4 and retList[i][3] == "blue":
                    blueString += " :trophy:"
            #Is red
            else:
                redString += retList[i][1] + " | "
                if i % 5 == 4 and retList[i][3] == "red":
                    redString += " :trophy:"

        totalStr += f"{gameIDstr}\n{blueString}\n{redString}\n\n"
        msg = discord.Embed(description=totalStr, color=discord.Color.gold())
        await ctx.send(embed=msg)
        cur.close()

    async def get_standing(self, ctx, requested_user: discord.Member):
        cur = self.get_cursor()
        cmd = f"SELECT name, win, loss, sp FROM players WHERE id ='{str(requested_user.id)}'"
        cur.execute(cmd)
        value = cur.fetchone()
        if value == None:
            await ctx.user.send("Player not found (They may not have played any games). If this is incorrect, please contact a staff member.")
            return

        win = value[1]
        loss = value[2]
        ratio = value[3]
        SP = value[4]
        name = value[0]
        msg = discord.Embed(color=discord.Color.gold())
        nameStr = name + "\n"
        SPstr = "**" + str(SP) + " SP** " + "\n"
        Ratstr = str(win) + "/" + str(loss) + " - " +str(ratio) + "% " + "\n"
        msg.add_field(name="Summoner", value=nameStr, inline=True)
        msg.add_field(name="Soulrush Points", value=SPstr, inline=True)
        msg.add_field(name="W/L", value=Ratstr, inline=True)
        
        # send standing as a DM to the requesting user
        await ctx.user.send(embed=msg)
        cur.close()
        