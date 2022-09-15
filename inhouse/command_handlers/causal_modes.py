import discord
from datetime import datetime
from inhouse.command_handlers.player import Player
import inhouse.constants
import inhouse.global_objects
from inhouse.command_handlers.queue import Queue, AramQueue
from riotwatcher import LolWatcher, ApiError

active_players_set: set = {}

class CasualLobby(object):
    def __init__(self, initiator_name: str, type: str) -> None:
        self.lol_api: LolWatcher = inhouse.global_objects.watcher
        self.initiator = initiator_name
        self.start_time_epoch = int(datetime.now().strftime('%s'))
        # people actively playing 
        self.active_player_names = [initiator_name]
        # total list of people who have played for rewards to be given
        self.participants = [initiator_name]
        self.thread: discord.Thread = None
        self.players_message: discord.message.Message = None
        self.type = type

        if type == 'ARAM':
            self.queue_ids = [450]
        elif type == 'Flex':
            self.queue_ids = [440]
        elif type == 'Normal':
            self.queue_ids = [400, 430]
        else:
            self.queue_ids = []

    async def add_player(self, player_name) -> bool:
        if len(self.active_player_names) == 5:
            return False

        if not player_name in self.active_player_names:
            self.active_player_names.append(player_name)
            # set check happens on button press so this is allowed
            active_players_set.add(player_name)

        if not player_name in self.participants:
            self.participants.append(player_name)
            
        await self.players_message.edit(f"Current Players: {', '.join(self.active_player_names)}")
        return True
    
    async def remove_player(self, player_name) -> bool:
        '''
        returns true to continue lobby, false to indicate that the lobby is done
        '''
        if player_name in self.active_player_names:
            self.active_player_names.remove(player_name)
            active_players_set.remove(player_name)
            await self.thread.send(f"{player_name} Left!")
            await self.players_message.edit(f"Current Players: {', '.join(self.active_player_names)}")

        return len(self.active_player_names) == 0

    async def create_thread(self, message: discord.Message):
        print("creating casual lobby thread")
        self.thread: discord.Thread = await message.create_thread(name=f"{self.initiator}'s {self.type} Lobby", auto_archive_duration=1440)
        # TODO: this should be a full instructions embed
        interactions_msg = await self.thread.send("After 6 hours no report :)", view=CasualLobbyInteractor(lobby=self))
        self.players_message = await self.thread.send(f"Current Players: {', '.join(self.active_player_names)}")
        await interactions_msg.pin()

    async def check_matches(self):
        if len(self.participants) < 2:
            print("not enough participants for rewards")
            await self.thread.send("In order to get rewards, you must have played with at least 1 game with 1 other server memeber")
            return

        player_id = self.lol_api.summoner.by_name(inhouse.constants.region, summoner_name=self.initiator)['puuid']
        print(f"got ID {player_id}")

        # Check for over 6 hours in which case we limit to the start + 6 hours to prevent abuse
        end_time_epoch = int(datetime.now().strftime('%s'))
        if end_time_epoch - self.start_time_epoch > inhouse.constants.casual_game_timeout:
            print("lobby has existed for over 6 hours, limiting to games within 6 hours of start...")
            end_time_epoch = self.start_time_epoch + inhouse.constants.casual_game_timeout

        # Find all matches for the given queue type
        # Could potentially just allow any type of game here as well
        match_ids_played_since_start = []
        for queue_id in self.queue_ids:
            match_ids_played_since_start += self.lol_api.match.matchlist_by_puuid(inhouse.constants.region, puuid=player_id, queue=queue_id, start_time=self.start_time_epoch, end_time=end_time_epoch)

        print(match_ids_played_since_start)
        games_to_credit_by_player = {}
        for match_id in match_ids_played_since_start:
            match = self.lol_api.match.by_id(region='na1', match_id=match_id)
            all_players = match['info']['participants']

            # match all the people who played from the server and mark how many games to credit for each
            for summoner in all_players: 
                summ_name = summoner['summonerName']
                if summ_name in self.participants:
                    games_to_credit_by_player[summ_name] = games_to_credit_by_player.get(summ_name, 0) + 1
        
        print("Done checking, would credit people here:")
        print(games_to_credit_by_player)
        # TODO: send rewards output here for people to know
        await self.thread.send(f"Done! Rewards have been granted to {', '.join(games_to_credit_by_player.keys())}")

        # remove remaining active players from the global set
        for remaining_player in self.active_player_names:
            active_players_set.remove(remaining_player)

        # clean up the thread?
       # await self.thread.delete()


class CasualModePicker(discord.ui.View):
    def __init__(self, *items, timeout = 180, ctx: discord.ApplicationContext):
        super().__init__(*items, timeout=timeout)
        self.ctx = ctx

    @discord.ui.button(label="Casual Inhouse - SR", style=discord.ButtonStyle.primary, emoji="⚔️")
    async def casual_inhouse_callback(self, button, interaction):
        await self.disable_buttons(interaction)
        print("Chose Casual Inhouses SR")
        if inhouse.global_objects.casual_queue != None:
            await inhouse.global_objects.casual_queue.queue_message.reply("Queue is already open! React to the above message")
            return
        inhouse.global_objects.casual_queue = Queue(ctx=self.ctx)
        await inhouse.global_objects.casual_queue.create_queue_message(inhouse.constants.server_roles.casual_inhouse)
        
    @discord.ui.button(label="Casual Inhouse - ARAM", style=discord.ButtonStyle.primary, emoji=f"<:ARAM:{inhouse.constants.aram_emoji_id}>")
    async def normal_game_callback(self, button, interaction):
        await self.disable_buttons(interaction)
        print("Chose Casual Inhouses ARAM")
        if inhouse.global_objects.casual_queue_aram != None:
            await inhouse.global_objects.casual_queue_aram.queue_message.reply("Queue is already open! React to the above message")
            return
        inhouse.global_objects.casual_queue_aram = AramQueue(ctx=self.ctx)
        await inhouse.global_objects.casual_queue_aram.create_queue_message(inhouse.constants.server_roles.casual_inhouse)

    @discord.ui.button(label="ARAM", style=discord.ButtonStyle.primary, emoji=f"<:ARAM:{inhouse.constants.aram_emoji_id}>")
    async def aram_callback(self, button, interaction):
        await self.disable_buttons(interaction)
        print("Chose ARAM")
        if interaction.user.display_name in active_players_set:
            await interaction.response.send_message("You are already in a lobby!")
            return
        # initialize lobby from user
        msg = discord.Embed(description=f"A Casual ARAM game is available! Join the thread **HERE** to play!", color=discord.Color.gold())
        message = await interaction.channel.send(f"{inhouse.global_objects.server_roles.aram.mention}", embed=msg)
        new_lobby = CasualLobby(initiator_name=interaction.user.display_name, type='ARAM')
        await new_lobby.create_thread(message)

    @discord.ui.button(label="FLEX", style=discord.ButtonStyle.primary, emoji="♻️")
    async def flex_callback(self, button, interaction):
        await self.disable_buttons(interaction)
        print("Chose Flex")
        if interaction.user.display_name in active_players_set:
            await interaction.response.send_message("You are already in a lobby!")
            return

        # initialize lobby from user
        msg = discord.Embed(description=f"A Casual Flex game is available! Join the thread **HERE** to play!", color=discord.Color.gold())
        message = await interaction.channel.send(f"{inhouse.global_objects.server_roles.flex.mention}", embed=msg)
        new_lobby = CasualLobby(initiator_name=interaction.user.display_name, type='Flex')
        await new_lobby.create_thread(message)

    @discord.ui.button(label="NORMAL GAMES", style=discord.ButtonStyle.primary, emoji="♻️")
    async def normals_callback(self, button, interaction):
        await self.disable_buttons(interaction)
        print("Chose Norms")
        if interaction.user.display_name in active_players_set:
            await interaction.response.send_message("You are already in a lobby!")
            return

        # initialize lobby from user
        msg = discord.Embed(description=f"A Casual Normal game is available! Join the thread **HERE** to play!", color=discord.Color.gold())
        message = await interaction.channel.send(f"{inhouse.global_objects.server_roles.normals.mention}", embed=msg)
        new_lobby = CasualLobby(initiator_name=interaction.user.display_name, type='Normal')
        await new_lobby.create_thread(message)

    async def disable_buttons(self, interaction):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)  

class CasualLobbyInteractor(discord.ui.View):
    def __init__(self, lobby):
        super().__init__(timeout=None)
        self.lobby: CasualLobby = lobby

    # TODO: add emoji
    @discord.ui.button(label="JOIN LOBBY", style=discord.ButtonStyle.green)
    async def join_lobby_callback(self, button, interaction):
        print("join lobby")
        if interaction.user.display_name in active_players_set:
            await interaction.response.send_message("You are already in a lobby!")

        success = await self.lobby.add_player(interaction.user.display_name)
        # disable join button if lobby full
        if not success:
            await interaction.response.send_message("Lobby is full! Check back later or start a new one!")
            print("Player cap reached")
        else:
            await interaction.response.send_message(f"{interaction.user.display_name} Joined!")

    @ discord.ui.button(label="LEAVE LOBBY", style=discord.ButtonStyle.red)
    async def leave_lobby_callback(self, button, interaction):
        print("leave lobby")
        await interaction.response.send_message("Left the lobby")
        finish_lobby = await self.lobby.remove_player(interaction.user.display_name)
        if finish_lobby:
            print("finishing...")
            await self.lobby.check_matches()

    @discord.ui.button(label="FINISH PLAYING", style=discord.ButtonStyle.primary)
    async def finish_lobby_callback(self, button, interaction):
        print("done")
        if not interaction.user.display_name in self.lobby.active_player_names:
            await interaction.response.send_message("Only players active in the lobby may mark it as finished.")
            return

        await interaction.response.send_message("Checking games...")
        await self.lobby.check_matches()
