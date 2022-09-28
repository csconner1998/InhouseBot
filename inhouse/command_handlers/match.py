from nis import match
import random
import discord
from .player import Player
from inhouse.constants import *
from inhouse.db_util import DatabaseHandler
import inhouse.global_objects
from datetime import datetime
import asyncio

class ActiveMatch(object):
    """
    Represents a currently active match, holding representations for:
    - match ID in DB
    - teams (by discord ID)
    - The match thread
    - a DB handler
    """
    def __init__(self, db_handler: DatabaseHandler, competitive: bool = False) -> None:
        print("creating new active match...")
        self.match_id = None
        self.db_handler = db_handler
        self.thread: discord.Thread = None
        self.blue_team: dict = None
        self.red_team: dict = None
        self.match_description_message: discord.Message = None
        self.original_thread_message: discord.Message = None
        self.is_test_match = False
        self.is_competitive_match = competitive

    # players is dict like { top: [Player, Player], jg: [jg1, jg2]... etc}
    async def begin(self, players: dict, ctx, madeMatch: bool = False):
        """
        Begins this match, setting up the thread, sending all info messages, and doing database operations
        """
        print("beginning match...")
        # Choose teams
        print(f"attempting start with players {players}")
        teams = self.choose_teams(players, madeMatch=madeMatch)
        self.blue_team = teams['blue']
        self.red_team = teams['red']
        self.player_ids = [player.id for role_list in players.values() for player in role_list]

        # DB Operations
        self.create_active_db_entry()

        # create thread
        await self.create_match_thread(ctx)

    def choose_teams(self, all_players: dict, madeMatch: bool = False) -> dict:
        """
        Helper to choose teams for this match randomly
        """
        print("choosing teams...")
        blue_team = {}
        red_team = {}
        for role, players in all_players.items():
            # shuffle and pop (not really that necessary for 2 element list but sue me)
            # dont shuffle if its a manually created match
            if not madeMatch:
                shuffled_players = random.sample(players, len(players))
            blue_team[role] = shuffled_players.pop()
            red_team[role] = shuffled_players.pop()
        return {'blue': blue_team, 'red': red_team}

    def get_empty_channels(self, ctx: discord.context.ApplicationContext):
        for channel_pair in voice_channels:
            blue_channel, red_channel = channel_pair
            blue_length = len(ctx.guild.get_channel(blue_channel).members)
            red_length = len(ctx.guild.get_channel(red_channel).members)
            if blue_length == 0 and red_length == 0:
                return channel_pair
        return ("","")
    
    async def create_match_thread(self, ctx: discord.context.ApplicationContext):
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
        await self.move_to_channels(ctx)
        await self.send_match_report_result()

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

    async def send_channel(self, member: discord.Member, channel: discord.VoiceChannel):
        print(f"member: {member}, channel: {channel}")
        try:
            await member.move_to(channel)
            return ""
        except Exception as e:
            print(e)
            if member != None and channel != None:
                return f"<@{member.id}> join <#{channel.id}>\n"
            else:
                return ""
            
    async def move_to_channels(self, ctx: discord.context.ApplicationContext):
        await asyncio.sleep(move_to_channel_delay)
        blue_channel_id, red_channel_id = self.get_empty_channels(ctx)
        if blue_channel_id == "" or red_channel_id == "":
            await self.thread.send("No Inhouse Channels Open")
            return
        ping_channel_string = ""
        for blue_player in self.blue_team.values():
            member = ctx.guild.get_member(blue_player.id) 
            channel = ctx.guild.get_channel(blue_channel_id)
            print(f"member: {member}, channel: {channel}")
            ping_channel_string += await self.send_channel(member,channel)
        for red_player in self.red_team.values():
            member = ctx.guild.get_member(red_player.id) 
            channel = ctx.guild.get_channel(red_channel_id) 
            print(f"member: {member}, channel: {channel}")
            ping_channel_string += await self.send_channel(member,channel)
        if ping_channel_string != "":
            await self.thread.send(ping_channel_string)
            
    async def send_match_report_result(self):
        """
        Sends the match report "report who won" message to the match thread
        """
        who_won = discord.Embed(description="Who Won?", color=discord.Color.gold())
        self.won_message = await self.thread.send(embed=who_won, view=ReportMatchResult(match=self))

    async def complete_match(self, winner: str):
        """
        Completes a match with the given winner, either 'red' or 'blue'
        """
        msg = discord.Embed(description=f":trophy: {winner.upper()} WINS! :trophy:", color=discord.Color.gold())
        await self.thread.send(embed=msg)

        # Always remove the active match
        remove_active_cur = self.db_handler.get_cursor()
        remove_active_match_sql = f"DELETE FROM active_matches WHERE active_id = '{self.match_id}'"
        self.db_handler.complete_transaction(remove_active_cur, [remove_active_match_sql])

        # if test/non-competitive match, lets not make a trip to the DB and stop here
        if self.is_test_match:
            await self.original_thread_message.delete()
            await self.won_message.delete()
            return

        # Update players in db
        if winner == 'blue':
            if self.is_competitive_match:
                inhouse.global_objects.coin_manager.update_all_member_coins(member_ids=[player.id for player in self.blue_team.values()], coin_amount=coins_for_competitive_inhouse_win)
                inhouse.global_objects.coin_manager.update_all_member_coins(member_ids=[player.id for player in self.red_team.values()], coin_amount=coins_for_competitive_inhouse_loss)
                [player.update_inhouse_standings('w') for player in self.blue_team.values()]
                [player.update_inhouse_standings('l') for player in self.red_team.values()]
            else:
                inhouse.global_objects.coin_manager.update_all_member_coins(member_ids=[player.id for player in self.blue_team.values()], coin_amount=coins_for_casual_inhouse_win)
                inhouse.global_objects.coin_manager.update_all_member_coins(member_ids=[player.id for player in self.red_team.values()], coin_amount=coins_for_casual_inhouse_loss)

        if winner == 'red':
            if self.is_competitive_match:
                inhouse.global_objects.coin_manager.update_all_member_coins(member_ids=[player.id for player in self.red_team.values()], coin_amount=coins_for_competitive_inhouse_win)
                inhouse.global_objects.coin_manager.update_all_member_coins(member_ids=[player.id for player in self.blue_team.values()], coin_amount=coins_for_competitive_inhouse_loss)
                [player.update_inhouse_standings('l') for player in self.blue_team.values()]
                [player.update_inhouse_standings('w') for player in self.red_team.values()]
            else:
                inhouse.global_objects.coin_manager.update_all_member_coins(member_ids=[player.id for player in self.red_team.values()], coin_amount=coins_for_casual_inhouse_win)
                inhouse.global_objects.coin_manager.update_all_member_coins(member_ids=[player.id for player in self.blue_team.values()], coin_amount=coins_for_casual_inhouse_loss)

        # if it's non-competitive, we can skip the rest of the DB stuff
        if not self.is_competitive_match:
            await self.original_thread_message.delete()
            await self.won_message.delete()
            return

        # update matches in db
        cur = self.db_handler.get_cursor()
        complete_match_sql = f"INSERT INTO matches(matchid, created, winner) VALUES ('{self.match_id}', '{str(datetime.now())}', '{winner}') RETURNING matchid"

        #insert players
        player_entries = ""
        for role, player in self.blue_team.items():
            player_entries += f"({self.match_id}, {player.id}, True, {role_str_to_db_id[role]}),"
        for role, player in self.red_team.items():
            player_entries += f"({self.match_id}, {player.id}, False, {role_str_to_db_id[role]}),"
        match_players_sql = f"INSERT INTO matches_players(match_id, player_id, blue, role) VALUES {player_entries.strip(',')}"

        self.db_handler.complete_transaction(cur, [complete_match_sql, match_players_sql])
        await self.original_thread_message.delete()
        await self.won_message.delete()
    
    async def swap_players(self, role: str):
        # Update model
        temp = self.blue_team[role]
        self.blue_team[role] = self.red_team[role]
        self.red_team[role] = temp

        # Update DB
        cur = self.db_handler.get_cursor()
        cmd = f"UPDATE active_matches SET {role}1 = {role}2, {role}2 = {role}1 WHERE active_id = {str(self.match_id)}"
        self.db_handler.complete_transaction(cur, [cmd])
        await self.send_match_description()
            
    def create_active_db_entry(self):
        """
        Helper to create an active_matches db entry for this match
        """
        if self.is_competitive_match:
            self.create_missing_players()

        player_ids_str = ""

        # if test/casual match, lets just make a dummy record in DB to store locally
        if self.is_test_match or not self.is_competitive_match:
            cmd = f"INSERT INTO active_matches(top1) VALUES (NULL) RETURNING active_id"
        else:
            for key in roles:
                player_ids_str += f"'{str(self.blue_team[key].id)}','{str(self.red_team[key].id)}',"

            # strip last comma and insert
            cmd = f"INSERT INTO active_matches({all_roles_db_key}) VALUES ({player_ids_str.strip(',')}) RETURNING active_id"

        cur = self.db_handler.get_cursor()
        cur.execute(cmd)
        # update match id
        self.match_id = cur.fetchone()[0]
        cur.close()
    
    def create_missing_players(self):
        all_players = self.get_all_players()
  
        cmd = f"SELECT id FROM players WHERE id IN {tuple([player.id for player in all_players])}"
        cur = self.db_handler.get_cursor()
        cur.execute(cmd)
        existing_player_ids = [existing_player[0] for existing_player in cur.fetchall()]

        for player in all_players:
            # Check if player is a Test player (aka has id of -1), in which case this is a test match and we can short-circuit
            if player.id == -1:
                return
            elif not player.id in existing_player_ids:
                # insert missing player
                insert_cmd = f"INSERT INTO players({new_player_db_key}) VALUES ('{player.id}', '{player.name}', '0', '0', '{default_points}')"
        
        self.db_handler.complete_transaction(cursor=cur, cmds=[insert_cmd])
            

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

# TODO: should overhaul this subclassing, lots of overrides/repeated code currently

class ActiveMatchARAM(ActiveMatch):
    def __init__(self, db_handler: DatabaseHandler, competitive: bool = False) -> None:
        super().__init__(db_handler, competitive)
        self.blue_team = []
        self.red_team = []
        self.match_id = ""

    async def begin(self, players: dict, ctx, madeMatch: bool = False):
        teams = self.choose_teams(all_players=players, madeMatch=madeMatch)
        self.blue_team = teams['blue']
        self.red_team = teams['red']
        # we skip DB entries for aram games
        await self.create_match_thread(ctx)

    def choose_teams(self, all_players: dict, madeMatch: bool = False) -> dict:
        players = all_players["all"]
        print(players)
        red_team = []
        shuffled_players = random.sample(players, len(players))
        for _ in range(0,5):
            red_team.append(shuffled_players.pop(0))
        blue_team = shuffled_players
        return {'blue': blue_team, 'red': red_team}

    async def send_match_description(self):
        msg = discord.Embed(description = "```ARAM!```",color=discord.Color.gold())

        blue_string = ""
        red_string = ""
        ping_string = ""
        for player in self.blue_team:
            blue_string += f"{player.name}\n"
            ping_string += f"<@{player.id}> "
        for player in self.red_team:
            red_string += f"{player.name}\n"
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
    
    def get_all_players(self) -> list:
        return [player for player in self.blue_team] + [player for player in self.red_team]

    async def move_to_channels(self, ctx: discord.context.ApplicationContext):
        await asyncio.sleep(move_to_channel_delay)
        blue_channel_id, red_channel_id = self.get_empty_channels(ctx)
        if blue_channel_id == "" or red_channel_id == "":
            self.thread.send("No Inhouse Channels Open")
            return
        ping_channel_string = ""
        for blue_player in self.blue_team:
            member = ctx.guild.get_member(blue_player.id) 
            channel = ctx.guild.get_channel(blue_channel_id)
            print(f"member: {member}, channel: {channel}")
            ping_channel_string += await self.send_channel(member,channel)
        for red_player in self.red_team:
            member = ctx.guild.get_member(red_player.id) 
            channel = ctx.guild.get_channel(red_channel_id) 
            print(f"member: {member}, channel: {channel}")
            ping_channel_string += await self.send_channel(member,channel)
        if ping_channel_string != "":
            await self.thread.send(ping_channel_string)

    async def complete_match(self, winner: str):
        print(f"completing ARAM match with winner {winner}")
        # real simple in the aram case, just send the tropy, update coins, and delete messages
        msg = discord.Embed(description=f":trophy: {winner.upper()} WINS! :trophy:", color=discord.Color.gold())
        if winner == 'blue':
                inhouse.global_objects.coin_manager.update_all_member_coins(member_ids=[player.id for player in self.blue_team.values()], coin_amount=coins_for_casual_inhouse_win)
                inhouse.global_objects.coin_manager.update_all_member_coins(member_ids=[player.id for player in self.red_team.values()], coin_amount=coins_for_casual_inhouse_loss)

        if winner == 'red':
                inhouse.global_objects.coin_manager.update_all_member_coins(member_ids=[player.id for player in self.red_team.values()], coin_amount=coins_for_casual_inhouse_win)
                inhouse.global_objects.coin_manager.update_all_member_coins(member_ids=[player.id for player in self.blue_team.values()], coin_amount=coins_for_casual_inhouse_loss)

        await self.thread.send(embed=msg)
        await self.original_thread_message.delete()
        await self.won_message.delete()

    async def send_match_report_result(self):
        who_won = discord.Embed(description="Who Won?", color=discord.Color.gold())
        await self.thread.send(embed=who_won, view=ReportMatchResult(match=self))




class ReportMatchResult(discord.ui.View):
    def __init__(self, match: ActiveMatch):
        super().__init__(timeout=None)
        self.match = match
    
    async def handle_complete_match(self, interaction: discord.Interaction, winner: str):
        try:
            if (self.match.is_competitive_match and "Match Reporter" in [role.name for role in interaction.user.roles]) or self.match.is_test_match:
                    # normal matches (need to have match reporter)
                    await self.match.complete_match(winner=winner)
                    inhouse.global_objects.main_queue.played_matches += 1
                    inhouse.global_objects.main_queue.active_matches.remove(self.match)
                    if inhouse.global_objects.main_leaderboard != None:
                        await inhouse.global_objects.main_leaderboard.update_leaderboard()
                        await interaction.response.defer()
                    else:
                        await interaction.response.send_message("Match has been recorded but Leaderboard channel is not set, ask Staff to set it!")
            elif not self.match.is_competitive_match:
                await self.match.complete_match(winner=winner)
                if isinstance(self.match, ActiveMatchARAM):
                    inhouse.global_objects.casual_queue_aram.active_matches.remove(self.match)
                else:
                    inhouse.global_objects.casual_queue.active_matches.remove(self.match)
                await interaction.response.defer()
            else:
                print("unhandled match case")
                await interaction.response.defer()
        except Exception as e:
            print(e)
            await interaction.response.send_message("Something went wrong! Please try again. If the issue persists, reach out to Staff.", ephemeral=True)

    @discord.ui.button(label="BLUE", style=discord.ButtonStyle.blurple)    
    async def blue_win_callback(self, button, interaction):
        print("Blue Win")
        await self.handle_complete_match(interaction=interaction, winner='blue')

    @discord.ui.button(label="RED", style=discord.ButtonStyle.red)    
    async def red_win_callback(self, button, interaction):
        print("Red Win")
        await self.handle_complete_match(interaction=interaction, winner='red')
