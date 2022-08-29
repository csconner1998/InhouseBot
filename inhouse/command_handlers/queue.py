
# There should only ever be one instance of this class per bot
from random import sample
from xmlrpc.client import boolean
import discord
from ..db_util import DatabaseHandler
from .match import ActiveMatch
from .leaderboard import Leaderboard
from .player import Player
import os
from ..constants import *

class Queue(object):
    """
    Represents the queue that players join to start games
    - Message ID of the queue
    - dictionary of active matches by ID
    - Players in the queue by role
    """
    def __init__(self, ctx: discord.context.ApplicationContext) -> None:
        # active matches should be {<message ID of match report>: Match object}
        self.active_matches_by_message_id = {}
        self.queued_players = {role_top: [], role_jungle: [], role_mid: [], role_adc: [], role_support: []}
        self.ctx = ctx
        # increments as matches are completed. Must be 1 or more to activate prio system
        self.played_matches = 0
        self.queue_message = None
        self.db_handler = DatabaseHandler(host=os.environ.get('DB_HOST'), db_name=os.environ.get('DB_NAME'), user=os.environ.get('DB_USER'), password=os.environ.get('DB_PASS'))

    async def create_queue_message(self, inhouse_role):
        """
        Should be called to create a new queue message
        """
        msg_str = f"```QUEUE```Top: <:Top:{top_emoji_id}>\nJungle: <:jungle:{jg_emoji_id}>\nMid: <:Mid:{mid_emoji_id}>\nAdc: <:Bottom:{bot_emoji_id}>\nSupport: <:Support:{supp_emoji_id}>"
        msg = discord.Embed(description=msg_str, color=discord.Color.gold())
        
        if inhouse_role == None:
            await self.ctx.send(content="InHouse role is not set, ask an admin to set it.")
            inhouse_role = ""

        message = await self.ctx.send(content=f"{inhouse_role} InHouse Queue is open!", embed=msg)
        self.queue_message = message

        # can maybe asyncio.gather these but runs into some REST overlap
        await self.queue_message.add_reaction(f"<:Top:{top_emoji_id}>")
        await self.queue_message.add_reaction(f"<:jungle:{jg_emoji_id}>")
        await self.queue_message.add_reaction(f"<:Mid:{mid_emoji_id}>")
        await self.queue_message.add_reaction(f"<:Bottom:{bot_emoji_id}>")
        await self.queue_message.add_reaction(f"<:Support:{supp_emoji_id}>")

    # resets the entire queue
    async def reset_queue(self, inhouse_role):
        """
        Reset everything in the queue and send a new message, deleting the old one

        NOTE: this does retain any currently active matches so that they can complete.
        """
        self.played_matches = 0
        for players in self.queued_players.values():
            del players[:]
        await self.queue_message.delete()
        await self.create_queue_message(inhouse_role)
    
    # stops the queue.
    async def stop_queue(self):
        """
        Stop everything in the queue

        NOTE: this does retain any currently active matches so that they can complete. HOWEVER, if a new queue is started, they will be lost.
        """
        for players in self.queued_players.values():
            del players[:]
        await self.queue_message.delete()

    async def attempt_create_match(self, bot: discord.Bot):
        """
        Checks if a match can be made and does if so, otherwise returns
        """
        print("attempting to create a match...")
        print(self.queued_players)
        if all(len(queued_for_role) >= 2 for queued_for_role in self.queued_players.values()):
            await self.create_match(bot)
    
    async def force_start(self, bot: discord.Bot):
        test_player = Player(-1,"Test Player",self.db_handler)
        for role, players in self.queued_players.items():
            if len(players) < 2:
                for i in range(2 - len(players)):
                    self.queued_players[role].append(test_player)
        print(self.queued_players)
        await self.create_match(bot, True)

        
    async def create_match(self, bot: discord.Bot, is_test: bool = False):
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
            keep_players = list(filter(lambda player: player.id not in match_player_ids, [player for player in self.queued_players[role]]))
            self.queued_players[role] = keep_players
        
        # create and begin match
        new_match = ActiveMatch(db_handler=self.db_handler)
        new_match.is_test_match = is_test
        report_message = await new_match.begin(players=match_players, ctx=self.ctx)

        # Add this match to the queue's tracker
        self.active_matches_by_message_id[report_message.id] = new_match

        # we do a get_message here to refresh the reaction cache so that we can use it to remove the correct ones
        # This avoids us having to map back to all the Discord User objects
        for reaction in bot.get_message(self.queue_message.id).reactions:
            player_reactions = await reaction.users().flatten()
            users_to_remove = [user for user in player_reactions if user.id in match_player_ids]
            for user in users_to_remove:
                await reaction.remove(user)
    
    async def attempt_complete_match(self, message_id, winner, main_leaderboard: Leaderboard):
        # if this really is a complete active match, complete it & update leaderboard. Otherwise this function is a no-op
        # clear the reactions first to stop people from multi-reacting & over-scoring
        match_to_finish = self.active_matches_by_message_id.pop(message_id)
        await match_to_finish.complete_match(winner)
        self.played_matches += 1

        if main_leaderboard != None:
            await main_leaderboard.update_leaderboard()
        else:
            await self.ctx.send("Match has been recorded but Leaderboard channel is not set, ask an Admin to set it!")
    
    # Utils
    def all_queued_player_ids(self) -> list:
        return [player.id for role_players in self.queued_players.values() for player in role_players]
