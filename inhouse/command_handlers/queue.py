
# There should only ever be one instance of this class per bot
from random import sample
import discord
from ..db_util import DatabaseHandler
from .match import ActiveMatch, ActiveMatchARAM
from .player import Player
from .leaderboard import Leaderboard
import os
from inhouse.constants import *

class Queue(object):
    """
    Represents the queue that players join to start games
    - Message ID of the queue
    - dictionary of active matches by ID
    - Players in the queue by role
    """
    def __init__(self, ctx: discord.context.ApplicationContext, competitive: bool = False) -> None:
        self.active_matches = []
        self.queued_players = {role_top: [], role_jungle: [], role_mid: [], role_adc: [], role_support: []}
        self.ctx = ctx
        # increments as matches are completed. Must be 1 or more to activate prio system
        self.played_matches = 0
        self.queue_message: discord.Message = None
        self.db_handler = DatabaseHandler(host=os.environ.get('DB_HOST'), db_name=os.environ.get('DB_NAME'), user=os.environ.get('DB_USER'), password=os.environ.get('DB_PASS'))
        # Marks if the queue is a competitive one, meaning we need to record things in the DB
        self.is_competitive_queue = competitive

    async def create_queue_message(self, inhouse_role: discord.Role):
        """
        Should be called to create a new queue message
        """
        msg_str = f'''
        ```QUEUE```
        **Top:** <:Top:{top_emoji_id}>
        **Jungle:** <:jungle:{jg_emoji_id}>
        **Mid:** <:Mid:{mid_emoji_id}>
        **Adc:** <:Bottom:{bot_emoji_id}>
        **Support:** <:Support:{supp_emoji_id}>
        '''

        msg = discord.Embed(description=msg_str, color=discord.Color.gold())
        
        if inhouse_role == None:
            await self.ctx.send(content="InHouse role is not set, ask an admin to set it.")
            inhouse_role = ""

        open_message = await self.ctx.send(content=f"{inhouse_role.mention} InHouse Queue is open!")
        q_message = await self.ctx.send(embed=msg)
        buttons_message = await self.ctx.send(view=InhouseQueueJoin(queue=self))
        self.queue_message = q_message
        self.messages_to_clean = [open_message, q_message, buttons_message]

    # resets the entire queue
    async def reset_queue(self, inhouse_role):
        """
        Reset everything in the queue and send a new message, deleting the old one

        NOTE: this does retain any currently active matches so that they can complete.
        """
        self.played_matches = 0
        for players in self.queued_players.values():
            del players[:]
        for msg in self.messages_to_clean:        
            await msg.delete()
        await self.create_queue_message(inhouse_role)
    
    # stops the queue.
    async def stop_queue(self):
        """
        Stop everything in the queue

        NOTE: this does retain any currently active matches so that they can complete. HOWEVER, if a new queue is started, they will be lost.
        """
        for players in self.queued_players.values():
            del players[:]
        for msg in self.messages_to_clean:        
            await msg.delete()

    async def attempt_create_match(self):
        """
        Checks if a match can be made and does if so, otherwise returns
        """
        print("attempting to create a match...")
        print(self.queued_players)
        if all(len(queued_for_role) >= 2 for queued_for_role in self.queued_players.values()):
            await self.create_match()
    
    async def force_start(self):
        test_player = Player(-1,"Test Player",self.db_handler)
        for role, players in self.queued_players.items():
            if len(players) < 2:
                for i in range(2 - len(players)):
                    self.queued_players[role].append(test_player)
        print(self.queued_players)
        await self.create_match(True)

    async def add_player_to_queue(self, player: Player, role: str):
        # Disallow players who are in an active match to queue
        match_player_ids = [match.get_all_player_ids() for match in self.active_matches]
        if len(match_player_ids) > 0 and player.id in match_player_ids[0]:
            print(f"{player.name} already in match")
            return

        # handle player swapping roles
        # this is a quasi-dangerous operation (modifying while looping), but it should short-circuit safely before any issue could arise
        to_remove_from_role = ""
        if player.id in self.all_queued_player_ids():
            print("already queued, swapping...")
            for existing_role, players in self.queued_players.items():
                if player.id in [p.id for p in players]:
                    print("found")
                    to_remove_from_role = existing_role
                    break

            # if they clicked the same role again, just exit
            if to_remove_from_role != role:
                print(f"swapping {player.name} from {to_remove_from_role} to {role}")
                found_players = list(filter(lambda existing_p: existing_p.id == player.id, [player for player in self.queued_players[to_remove_from_role]]))
                self.queued_players[to_remove_from_role].remove(found_players[0])
                print("removed")
            else:
                print("already queued as role")
                return

        self.queued_players[role].append(player)
        await self.attempt_create_match()

    async def remove_player_from_queue(self, player_id: int):
        to_remove_from_role = ""
        for role, existing_players in self.queued_players.items():
            if player_id in [p.id for p in existing_players]:
                to_remove_from_role = role
                break
        
        found_players = list(filter(lambda existing_p: existing_p.id == player_id, [player for player in self.queued_players[to_remove_from_role]]))
        self.queued_players[to_remove_from_role].remove(found_players[0])
        print(self.queued_players)

    async def manual_create_match(self, playerList, is_test : bool = False):
        """
        Creates a new ActiveMatch from players in playerList.
        """
        match_players = {role_top: [], role_jungle: [], role_mid: [], role_adc: [], role_support: []}
        # store the ids as just a list for pruning the reactions later

        for role, players in playerList.items():
            match_players[role].append(players.pop(0))
            match_players[role].append(players.pop(0))
        
        # create and begin match
        new_match = ActiveMatch(db_handler=self.db_handler, competitive=self.is_competitive_queue)
        new_match.is_test_match = is_test
        await new_match.begin(players=match_players, ctx=self.ctx)

        # Add this match to the queue's tracker
        self.active_matches.append(new_match)

    async def create_match(self, is_test : bool = False):
        """
        Creates a new ActiveMatch from players in the queue. Should be triggered when an appropriate number of players is reached.
        Handles player priority as well as reaction cleanup for players selected.
        """

        match_players = {role_top: [], role_jungle: [], role_mid: [], role_adc: [], role_support: []}
        # store the ids as just a list for pruning the reactions later
        match_player_ids = []

        for role, players in self.queued_players.items():
            if self.played_matches > 0:
                # if at least one match has been completed, we use the queue as an actual queue rather than selecting randomly
                match_players[role].append(players.pop(0))
                match_players[role].append(players.pop(0))
            else:
                # otherwise just choose 2 per role at random
                match_players[role] = sample(players, 2)
            for player in match_players[role]:
                if player.id != -1:
                    match_player_ids.append(player.id)

        # remove selected players from internal queue representation
        for role in roles:
            keep_players = list(filter(lambda player: player.id not in match_player_ids and player.id != -1, [player for player in self.queued_players[role]]))
            self.queued_players[role] = keep_players
            
        # create and begin match
        new_match = ActiveMatch(db_handler=self.db_handler, competitive=self.is_competitive_queue)
        new_match.is_test_match = is_test
        await new_match.begin(players=match_players, ctx=self.ctx)

        # Add this match to the queue's tracker
        self.active_matches.append(new_match)
        await self.update_queue_message()
    
    async def update_queue_message(self):
        msg_str = f'''```QUEUE```
        **Top** <:Top:{top_emoji_id}> {','.join([player.name for player in self.queued_players[role_top]])}
        **Jungle** <:jungle:{jg_emoji_id}> {','.join([player.name for player in self.queued_players[role_jungle]])}
        **Mid** <:Mid:{mid_emoji_id}> {','.join([player.name for player in self.queued_players[role_mid]])}
        **Adc** <:Bottom:{bot_emoji_id}> {','.join([player.name for player in self.queued_players[role_adc]])}
        **Support** <:Support:{supp_emoji_id}> {','.join([player.name for player in self.queued_players[role_support]])}
        '''
        msg = discord.Embed(description=msg_str, color=discord.Color.gold())
        await self.queue_message.edit(embed=msg)
    
    # Utils
    def all_queued_player_ids(self) -> list:
        return [player.id for role_players in self.queued_players.values() for player in role_players]


class AramQueue(Queue):
    def __init__(self, ctx: discord.context.ApplicationContext, competitive: bool = False) -> None:
        super().__init__(ctx, competitive)
        self.queued_players = {"all": []}

    async def create_queue_message(self, inhouse_role: discord.Role):
        msg_str = f"```ARAM QUEUE```React to Play: <:ARAM:{aram_emoji_id}>\n"
        msg = discord.Embed(description=msg_str, color=discord.Color.gold())
        
        if inhouse_role == None:
            await self.ctx.send(content="InHouse role is not set, ask an admin to set it.")
            inhouse_role = ""

        message = await self.ctx.send(content=f"{inhouse_role.mention} ARAM InHouse Queue is open!", embed=msg)
        self.queue_message = message

        await self.queue_message.add_reaction(f"<:ARAM:{aram_emoji_id}>")


    async def attempt_create_match(self):
        print("attempting to create an ARAM match...")
        if len(self.queued_players["all"]) == 10:
            await self.create_match()
    
    async def create_match(self, is_test: bool = False):            
        # create and begin match
        new_match = ActiveMatchARAM(db_handler=self.db_handler, competitive=False)
        new_match.is_test_match = is_test
        await new_match.begin(players=self.queued_players, ctx=self.ctx)

        # remove  players from internal queue representation
        self.queued_players["all"].clear()

        # Add this match to the queue's tracker
        self.active_matches.append(new_match)

    def all_queued_player_ids(self) -> list:
        return [player.id for player in self.queued_players["all"]]

class InhouseQueueJoin(discord.ui.View):
    def __init__(self, queue: Queue):
        super().__init__(timeout=None)
        self.queue = queue
    
    async def add_to_queue(self, interaction: discord.Interaction, role: str):
        try:
            await self.queue.add_player_to_queue(Player(id=interaction.user.id, name=interaction.user.display_name, db_handler=self.queue.db_handler), role=role)
            await interaction.response.defer()
        except Exception as e:
            print(e)
            await interaction.response.send_message("Something went wrong! Please try again. If the issue persists, reach out to Staff.", ephemeral=True)
        
        await self.queue.update_queue_message()
    
    @discord.ui.button(label="TOP", style=discord.ButtonStyle.secondary, emoji=f"<:Top:{top_emoji_id}>")
    async def queue_top_callback(self, button, interaction):
        print("Queue Top")
        await self.add_to_queue(interaction=interaction, role=role_top)

    @discord.ui.button(label="JUNGLE", style=discord.ButtonStyle.secondary, emoji=f"<:Jungle:{jg_emoji_id}>")    
    async def queue_jungle_callback(self, button, interaction):
        print("Queue JG")
        await self.add_to_queue(interaction=interaction, role=role_jungle)

    @discord.ui.button(label="MID", style=discord.ButtonStyle.secondary, emoji=f"<:Mid:{mid_emoji_id}>")    
    async def queue_mid_callback(self, button, interaction):
        print("Queue Mid")
        await self.add_to_queue(interaction=interaction, role=role_mid)

    @discord.ui.button(label="BOTTOM", style=discord.ButtonStyle.secondary, emoji=f"<:Bottom:{bot_emoji_id}>")    
    async def queue_bottom_callback(self, button, interaction):
        print("Queue Bot")
        await self.add_to_queue(interaction=interaction, role=role_adc)

    @discord.ui.button(label="SUPPORT", style=discord.ButtonStyle.secondary, emoji=f"<:Support:{supp_emoji_id}>")    
    async def queue_support_callback(self, button, interaction):
        print("Queue Supp")
        await self.add_to_queue(interaction=interaction, role=role_support)

    @discord.ui.button(label="LEAVE QUEUE", style=discord.ButtonStyle.red)    
    async def leave_queue_callback(self, button, interaction):
        print("Leave Queue")
        try:
            await self.queue.remove_player_from_queue(player_id=interaction.user.id)
            await interaction.response.send_message(f"You left the queue", ephemeral=True)
        except Exception as e:
            print(e)
            await interaction.response.send_message("Something went wrong! Please try again. If the issue persists, reach out to Staff.", ephemeral=True)

        await self.queue.update_queue_message()