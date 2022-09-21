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

    def complete_transaction(self, cursor):
        self.connection.commit()
        cursor.close()

    async def get_names(self):
        cur = self.get_cursor()
        cmd = "SELECT league_name FROM soloqueue_leaderboard;"
        cur.execute(cmd)
        retList = cur.fetchall()
        return retList

    async def set_show_rank(self,id,name,opt):
        cur = self.get_cursor()
        if opt:
            cmd = f"INSERT into soloqueue_leaderboard(discord_id,league_name) VALUES ('{id}', '{name}');"
        else:
            cmd = f"DELETE FROM soloqueue_leaderboard WHERE discord_id = '{id}'"
        cur.execute(cmd)
        self.complete_transaction(cur)
        
    async def get_match_history(self, ctx, count):
        cur = self.get_cursor()
        cmd = f"SELECT match_id, name, blue, winner FROM matches_players INNER JOIN players ON matches_players.player_id = players.id inner join matches on matches_players.match_id = matches.matchid ORDER BY matches.matchid DESC, blue ASC limit {count*10};"
        cur.execute(cmd)
        retList = cur.fetchall()
        totalStr = "```Match History```"
        gameIDstr = ""
        blueString = ""
        redString = ""
        for i in range(len(retList)):
            if i % 10 == 0:
                if i != 0:
                    totalStr += f"{gameIDstr}\n{blueString}\n{redString}\n\n"
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
        self.complete_transaction(cur)