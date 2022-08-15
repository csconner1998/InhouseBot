from array import array
from dis import disco
from mimetypes import init
import random
import discord
import math
from .player import Player
from inhouse.constants import *
from inhouse.db_util import DatabaseHandler
from datetime import datetime

class ActiveMatch(object):
    """
    Represents a currently active match, holding representations for:
    - match ID in DB
    - teams (by discord ID)
    - The match thread
    - a DB handler
    """
    def __init__(self, db_handler: DatabaseHandler) -> None:
        print("creating new active match...")
        self.match_id = None
        self.db_handler = db_handler
        self.thread: discord.Thread = None
        self.blue_team: dict = None
        self.red_team: dict = None
        self.match_description_message: discord.Message = None
        self.original_thread_message: discord.Message = None

    # players is dict like { top: [Player, Player], jg: [jg1, jg2]... etc}
    async def begin(self, players: dict, ctx) -> discord.Message:
        """
        Begins this match, setting up the thread, sending all info messages, and doing database operations
        """
        print("beginning match...")
        # Choose teams
        print(f"attempting start with players {players}")
        teams = self.choose_teams(players)
        self.blue_team = teams['blue']
        self.red_team = teams['red']
        self.player_ids = [player.id for role_list in players.values() for player in role_list]

        # DB Operations
        self.create_active_db_entry()

        # create thread
        return await self.create_match_thread(ctx)

    def choose_teams(self, all_players: dict) -> dict:
        """
        Helper to choose teams for this match randomly
        """
        print("choosing teams...")
        blue_team = {}
        red_team = {}
        for role, players in all_players.items():
            # shuffle and pop (not really that necessary for 2 element list but sue me)
            shuffled_players = random.sample(players, len(players))
            blue_team[role] = shuffled_players.pop()
            red_team[role] = shuffled_players.pop()
        return {'blue': blue_team, 'red': red_team}

    async def create_match_thread(self, ctx: discord.context.ApplicationContext) -> discord.Message:
        """
        Helper to create a new discord thread for the match. Threads are set to auto-archive in 2 hours

        Returns the Message object of the "report result"
        """
        print("creating match thread...")
        msg = discord.Embed(description=f"Match {self.match_id} has started! Join the Thread **HERE!**", color=discord.Color.gold())
        start_message = await ctx.send(embed=msg)
        # auto archive in 1 hour of inactivity
        self.thread: discord.Thread = await start_message.create_thread(name=f"Game {self.match_id}", auto_archive_duration=60)
        self.original_thread_message = start_message
        await self.send_match_description()
        return await self.send_match_report_result()

    async def send_match_description(self):
        """
        Sends the match description including roles/players and match number to the match thread
        """
        msg = discord.Embed(description = "```Game "+ str(self.match_id) +"```",color=discord.Color.gold())

        blue_string = ""
        red_string = ""
        ping_string = ""
        for role, player in self.blue_team.items():
            blue_string += f"{role}: {player.name}\n"
            ping_string += f"<@{player.id}> "
        for role, player in self.red_team.items():
            red_string += f"{role}: {player.name}\n"
            ping_string += f"<@{player.id}> "

        msg.add_field(name="Blue Team", value=blue_string.strip(), inline=True)
        msg.add_field(name="Red Team", value=red_string.strip(), inline=True)
        match_desc = await self.thread.send(embed=msg)

        # unpin old (if applicable) and pin new
        if self.match_description_message != None:
            await self.match_description_message.unpin()
        else:
            # send the ping string if this is the first match desc
            await self.thread.send(ping_string)

        await match_desc.pin()
        self.match_description_message = match_desc

    async def send_match_report_result(self) -> discord.Message:
        """
        Sends the match report "report who won" message to the match thread
        """
        cur = self.db_handler.get_cursor()
        who_won = discord.Embed(description="Who Won?", color=discord.Color.gold())
        won_message = await self.thread.send(embed=who_won)
        cmd = f"UPDATE active_matches SET win_msg_id = '{str(won_message.id)}' where active_id = '{str(self.match_id)}'"
        cur.execute(cmd)
        self.db_handler.complete_transaction(cur)
        await won_message.add_reaction("🟦")
        await won_message.add_reaction("🟥")
        return won_message

    async def complete_match(self, winner: str):
        """
        Completes a match with the given winner, either 'red' or 'blue'
        """        
        # Update players in db
        if winner == 'blue':
            [player.update_player_in_db('w') for player in self.blue_team.values()]
            [player.update_player_in_db('l') for player in self.red_team.values()]
        if winner == 'red':
            [player.update_player_in_db('l') for player in self.blue_team.values()]
            [player.update_player_in_db('w') for player in self.red_team.values()]

        # update matches in db
        cur = self.db_handler.get_cursor()
        complete_match_sql = f"INSERT INTO matches(matchid, created, winner) VALUES ('{self.match_id}', '{str(datetime.now())}', '{winner}') RETURNING matchid"
        remove_active_match_sql = f"DELETE FROM active_matches WHERE active_id = '{self.match_id}'"

        #insert players
        player_entries = ""
        for role, player in self.blue_team.items():
            player_entries += f"({self.match_id}, {player.id}, True, {role_str_to_db_id[role]}),"
        for role, player in self.red_team.items():
            player_entries += f"({self.match_id}, {player.id}, False, {role_str_to_db_id[role]}),"
        match_players_sql = f"INSERT INTO matches_players(match_id, player_id, blue, role) VALUES {player_entries.strip(',')}"

        cur.execute(complete_match_sql)
        cur.execute(match_players_sql)
        cur.execute(remove_active_match_sql)
        self.db_handler.complete_transaction(cur)
        await self.original_thread_message.delete()
        logger.debug("done creating match.")
    
    async def swap_players(self, role: str):
        logger.debug(f"swapping players for {role}")
        # Update model
        temp = self.blue_team[role]
        self.blue_team[role] = self.red_team[role]
        self.red_team[role] = temp

        # Update DB
        cur = self.db_handler.get_cursor()
        cmd = f"UPDATE active_matches SET {role}1 = {role}2, {role}2 = {role}1 WHERE active_id = {str(self.match_id)}"
        print(cmd)
        cur.execute(cmd)
        self.db_handler.complete_transaction(cur)
        await self.send_match_description()
            
    def create_active_db_entry(self):
        """
        Helper to create an active_matches db entry for this match
        """
        self.create_missing_players()

        player_ids_str = ""
        for key in roles:
            player_ids_str += f"'{str(self.blue_team[key].id)}','{str(self.red_team[key].id)}',"
        
        # strip last comma and insert
        cmd = f"INSERT INTO active_matches({all_roles_db_key}) VALUES ({player_ids_str.strip(',')}) RETURNING active_id"

        cur = self.db_handler.get_cursor()
        cur.execute(cmd)
        # update match id
        self.match_id = cur.fetchone()[0]
        self.db_handler.complete_transaction(cur)
    
    def create_missing_players(self):
        all_players = self.get_all_players()
  
        cmd = f"SELECT id FROM players WHERE id IN {tuple([player.id for player in all_players])}"
        cur = self.db_handler.get_cursor()
        cur.execute(cmd)
        existing_player_ids = [existing_player[0] for existing_player in cur.fetchall()]

        for player in all_players:
            if not player.id in existing_player_ids:
                # insert missing player
                insert_cmd = f"INSERT INTO players({new_player_db_key}) VALUES ('{player.id}', '{player.name}', '0', '0', '0', '{default_points}')"
                cur.execute(insert_cmd)
        
        self.db_handler.complete_transaction(cursor=cur)
            

    # Utils
    def get_all_players(self) -> list:
        return [player for player in self.blue_team.values()] + [player for player in self.red_team.values()]
    
    def get_all_player_ids(self) -> list:
        return [player.id for player in self.get_all_players()]

    def print_match_debug(self):
        """
        Dump all match stuff for debug
        """
        print(f"""ID: {self.id}
        Blue Team: {self.blue_team}
        Red Team: {self.red_team}
        Thread ID: {self.thread.id}""")




        

async def getMatchHistory(ctx, db_handler, count):
    await ctx.message.delete()
    cur = db_handler.getCursor()
    cmd = f"SELECT match_id, name, blue, winner FROM matches_players INNER JOIN players ON matches_players.player_id = players.id inner join matches on matches_players.match_id = matches.matchid ORDER BY matches.matchid DESC, blue ASC limit {count};"
    cur.execute(cmd)
    retList = cur.fetchall()
    totalStr = "```Match History```"
    gameIDstr = ""
    blueString = ""
    redString = ""
    for i in range(len(retList)):
        if i % 10 == 0:
            if i != 0:
                totalStr += gameIDstr + "\n" + blueString + "\n" + redString + "\n\n"
            gameIDstr="**__Game ID: " + str(retList[i][0]) + "__**"
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
    totalStr += gameIDstr + "\n" + blueString + "\n" + redString + "\n\n"
    msg = discord.Embed(description=totalStr, color=discord.Color.gold())
    await ctx.send(embed=msg)
    cur.close()
