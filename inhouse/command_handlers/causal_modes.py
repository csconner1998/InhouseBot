from http import server
import discord
from datetime import datetime
from inhouse.command_handlers.player import Player
import inhouse.constants
import inhouse.global_objects
from inhouse.command_handlers.queue import Queue, AramQueue
from riotwatcher import LolWatcher, ApiError

active_players_set: set = set()

class CasualLobby(object):
    def __init__(self, initiator_name: str, game_type: str) -> None:
        self.lol_api: LolWatcher = inhouse.global_objects.watcher
        self.initiator = initiator_name
        self.start_time_epoch = int(datetime.now().strftime('%s'))
        # people actively playing 
        self.active_player_names = [initiator_name]
        active_players_set.add(initiator_name)
        # total list of people who have played for rewards to be given
        self.participants = [initiator_name]
        self.thread: discord.Thread = None
        self.players_message: discord.message.Message = None
        self.original_thread_message: discord.Message = None
        self.lobby_type = game_type

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
        returns false to continue lobby, true to indicate that the lobby is done
        '''
        if player_name in self.active_player_names:
            self.active_player_names.remove(player_name)
            active_players_set.discard(player_name)
            await self.thread.send(f"{player_name} Left!")
            await self.players_message.edit(f"Current Players: {', '.join(self.active_player_names)}")

        return len(self.active_player_names) == 0

    async def create_thread(self, message: discord.Message):
        print("creating casual lobby thread")
        self.original_thread_message = message
        self.thread: discord.Thread = await message.create_thread(name=f"NOW PLAYING - {self.lobby_type}", auto_archive_duration=1440)
        embed_msg = discord.Embed(title="INSTRUCTIONS",description=f'''
        1. Use the buttons below to join or leave the lobby.
        2. Hop on to League and play some games!
        3. When you're done, press the "Finish Playing" button to receive your rewards.


        FAQ:
        - Any players that participate over the course of the lobby will be given rewards (even if you leave after only a game or two).
        - The original creator does not need to play the entire time, they can leave just like anyone else.
        - Lobbies are limited to 6 hours to prevent abuse. When the bot checks for rewards, it will only look for games started within 6 hours of this lobby being created.
        - In order to receive rewards, your discord nickname **MUST** match your League of Legends summoner name. Use the `/setname` command in <#{inhouse.constants.name_assign_channel}> if you need.
        - The bot is smart enough to recognize other types of games played. This means that you don't need to start a new lobby when changing game types. For example, if this is an ARAM lobby and you play a couple of normal games in between, those will still be counted.
        - Occassionally, the Riot API is slow to update. If you did not receive rewards for a particular game you played, please reach out to staff.
        ''', color=discord.Color.dark_purple())
        interactions_msg = await self.thread.send(embed=embed_msg, view=CasualLobbyInteractor(lobby=self))
        self.players_message = await self.thread.send(f"Current Players: {', '.join(self.active_player_names)}")
        await interactions_msg.pin()

    async def change_lobby_type(self, new_type: str):
        print(f"changing lobby to {new_type}...")
        self.lobby_type = new_type
        await self.thread.edit(name=f"NOW PLAYING - {self.lobby_type}")
        print("done changing lobby")

    async def check_matches(self):
        if len(self.participants) < 1:
            print("not enough participants for rewards")
            await self.thread.send("In order to get rewards, you must have played with at least 1 game with 1 other server member")
            await self.original_thread_message.delete()
            return

        player_ids = []
        for player in self.participants:
            player_id = self.lol_api.summoner.by_name(inhouse.constants.region, summoner_name=self.initiator)['puuid']
            print(f"got ID {player_id}")
            player_ids.append(player_id)

        print(player_ids)
        # Check for over 6 hours in which case we limit to the start + 6 hours to prevent abuse
        end_time_epoch = int(datetime.now().strftime('%s'))
        if end_time_epoch - self.start_time_epoch > inhouse.constants.casual_game_timeout:
            print("lobby has existed for over 6 hours, limiting to games within 6 hours of start...")
            end_time_epoch = self.start_time_epoch + inhouse.constants.casual_game_timeout

        # Find all matches within the lobby lifespan for each participant
        all_match_ids_played = []
        for player_id in player_ids:
            all_match_ids_played += self.lol_api.match.matchlist_by_puuid(inhouse.constants.region, puuid=player_id, start_time=self.start_time_epoch, end_time=end_time_epoch)
        
        # Make a set of the unique matches played since the start
        match_ids_played_since_start = set(all_match_ids_played)
        print(match_ids_played_since_start)
        games_to_credit_by_player = {}
        for match_id in match_ids_played_since_start:
            match = self.lol_api.match.by_id(region='na1', match_id=match_id)
            all_players = match['info']['participants']

            # match all the people who played from the server in each game
            server_players = []
            for summoner in all_players: 
                summ_name = summoner['summonerName']
                if summ_name in self.participants:
                    server_players.append(summ_name)

            print(server_players)
            # make sure there were actually 2 or more players from the server in the game before giving credit
            if len(server_players) >= 1:
                for summoner in server_players:    
                    games_to_credit_by_player[summoner] = games_to_credit_by_player.get(summoner, 0) + 1
        
        print("Done checking, credit people here:")
        print(games_to_credit_by_player)

        embed_msg = discord.Embed(description="", color=discord.Color.gold())
        for player, game_count in games_to_credit_by_player.items():
            embed_msg.add_field(name="Player", value=player, inline=True)
            embed_msg.add_field(name="Games Played", value=game_count, inline=True)
            embed_msg.add_field(name="Wonkoin Earned", value=game_count * inhouse.constants.coins_for_casual_game, inline=True)
            
            member = self.thread.guild.get_member_named(name=player)
            if not member == None: 
                inhouse.global_objects.coin_manager.update_member_coins(member=member, coin_amount=game_count * inhouse.constants.coins_for_casual_game)
            else:
                print(f"could not find member {player}, did not update coins")

        await self.thread.send(f"Done! Rewards have been granted!", embed=embed_msg)

        # remove remaining active players from the global set
        for remaining_player in self.active_player_names:
            active_players_set.discard(remaining_player)

        await self.original_thread_message.delete()
        await self.thread.archive()


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
        msg = discord.Embed(description=f"{interaction.user.display_name}'s Lobby. Join the thread to play!", color=discord.Color.gold())
        message = await interaction.channel.send(f"{inhouse.global_objects.server_roles.aram.mention}", embed=msg)
        new_lobby = CasualLobby(initiator_name=interaction.user.display_name, game_type='ARAM')
        await new_lobby.create_thread(message)

    @discord.ui.button(label="FLEX", style=discord.ButtonStyle.primary, emoji="💪")
    async def flex_callback(self, button, interaction):
        await self.disable_buttons(interaction)
        print("Chose Flex")
        if interaction.user.display_name in active_players_set:
            await interaction.response.send_message("You are already in a lobby!")
            return

        # initialize lobby from user
        msg = discord.Embed(description=f"{interaction.user.display_name}'s Lobby. Join the thread to play!", color=discord.Color.gold())
        message = await interaction.channel.send(f"{inhouse.global_objects.server_roles.flex.mention}", embed=msg)
        new_lobby = CasualLobby(initiator_name=interaction.user.display_name, game_type='Flex')
        await new_lobby.create_thread(message)

    @discord.ui.button(label="NORMAL GAMES", style=discord.ButtonStyle.primary, emoji="🎮")
    async def normals_callback(self, button, interaction):
        await self.disable_buttons(interaction)
        print("Chose Norms")
        if interaction.user.display_name in active_players_set:
            await interaction.response.send_message("You are already in a lobby!")
            return

        # initialize lobby from user
        msg = discord.Embed(description=f"{interaction.user.display_name}'s Lobby. Join the thread to play!", color=discord.Color.gold())
        message = await interaction.channel.send(f"{inhouse.global_objects.server_roles.normals.mention}", embed=msg)
        new_lobby = CasualLobby(initiator_name=interaction.user.display_name, game_type='Normal')
        await new_lobby.create_thread(message)

    async def disable_buttons(self, interaction):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)  

class CasualLobbyInteractor(discord.ui.View):
    def __init__(self, lobby):
        super().__init__(timeout=None)
        self.lobby: CasualLobby = lobby

    @discord.ui.button(label="JOIN LOBBY", style=discord.ButtonStyle.green)
    async def join_lobby_callback(self, button, interaction):
        print("join lobby")
        if interaction.user.display_name in active_players_set:
            await interaction.response.send_message("You are already in a lobby!")
            return

        success = await self.lobby.add_player(interaction.user.display_name)
        # disable join button if lobby full
        if not success:
            await interaction.response.send_message("Lobby is full! Check back later or start a new one!")
            print("Player cap reached")
        else:
            await interaction.response.send_message(f"{interaction.user.display_name} Joined!")

    @discord.ui.button(label="LEAVE LOBBY", style=discord.ButtonStyle.red)
    async def leave_lobby_callback(self, button, interaction):
        print("leave lobby")
        finish_lobby = await self.lobby.remove_player(interaction.user.display_name)
        if finish_lobby:
            print("finishing...")
            await self.lobby.check_matches()
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(view=self)
        else:
            await interaction.response.send_message("Left the lobby")
    
    @discord.ui.button(label="CHANGE LOBBY TYPE", style=discord.ButtonStyle.gray)
    async def change_lobby_type_callback(self, button, interaction):
        print("change lobby type")
        await interaction.response.send_message("What do you wany to play instead?", view=CasualLobbyChangeModeInteractor(timeout=60, lobby=self.lobby))

    @discord.ui.button(label="FINISH PLAYING", style=discord.ButtonStyle.primary)
    async def finish_lobby_callback(self, button, interaction):
        print("done")
        if not interaction.user.display_name in self.lobby.active_player_names:
            await interaction.response.send_message("Only players active in the lobby may mark it as finished.")
            return

        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)

        await self.lobby.check_matches()


class CasualLobbyChangeModeInteractor(discord.ui.View):
    def __init__(self, timeout, lobby):
        super().__init__(timeout=timeout)
        self.lobby: CasualLobby = lobby
    
    @discord.ui.button(label="ARAM", style=discord.ButtonStyle.primary, emoji=f"<:ARAM:{inhouse.constants.aram_emoji_id}>")
    async def change_to_aram_callback(self, button, interaction):
        if not interaction.user.display_name in self.lobby.active_player_names:
            await interaction.response.send_message("Only active players may change the lobby type.")
            return
        if self.lobby.lobby_type == 'ARAM':
            await interaction.response.send_message("Already an ARAM lobby.")
            return
       
       # update lobby
        await self.lobby.change_lobby_type(new_type='ARAM')
        await self.disable_buttons(interaction)

    @discord.ui.button(label="FLEX", style=discord.ButtonStyle.primary, emoji="💪")
    async def change_to_flex_callback(self, button, interaction):
        if not interaction.user.display_name in self.lobby.active_player_names:
            await interaction.response.send_message("Only active players may change the lobby type.")
            return
        if self.lobby.lobby_type == 'Flex':
            await interaction.response.send_message("Already a Flex lobby.")
            return
       
       # update lobby
        await self.lobby.change_lobby_type(new_type='Flex')
        await self.disable_buttons(interaction)


    @discord.ui.button(label="NORMAL GAMES", style=discord.ButtonStyle.primary, emoji="🎮")
    async def change_to_normals_callback(self, button, interaction):
        if not interaction.user.display_name in self.lobby.active_player_names:
            await interaction.response.send_message("Only active players may change the lobby type.")
            return
        if self.lobby.lobby_type == 'Normal':
            await interaction.response.send_message("Already a Normal lobby.")
            return
       
       # update lobby
        await self.lobby.change_lobby_type(new_type='Normal')
        await self.disable_buttons(interaction)

    async def disable_buttons(self, interaction):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)  