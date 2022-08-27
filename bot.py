import discord
from discord.ext import commands
import re
import os
from inhouse.command_handlers.causal_modes import CasualModePicker
from inhouse.command_handlers.player import Player
from riotwatcher import LolWatcher, ApiError

# TODO: logger rather than prints

from inhouse.db_util import DatabaseHandler 
from inhouse.constants import *
from inhouse.command_handlers.queue import Queue
from inhouse.command_handlers.leaderboard import Leaderboard
from inhouse.command_handlers.soloqueue_leaderboard import Soloqueue_Leaderboard

""" SEQUENCE (v1):
1) Bot executable starts
2) User types !queue start
3) Bot creates a single queue and does all its setup. There should only ever be 1 queue per server (IMO)
4) As users react, on_raw_reaction_add checks against the known messages for:
    - The Queue
    - Any Match reports
5) If the reaction is to one of these, the appropriate behavior is called on the queue:
    - Queue.attempt_create_match() for the Queue
    - Queue.complete_match(message_id, winner) for any match report

"""
db_handler = DatabaseHandler(host=os.environ.get('DB_HOST'), db_name=os.environ.get(
    'DB_NAME'), user=os.environ.get('DB_USER'), password=os.environ.get('DB_PASS'))
# Limits us to just 1 server so that slash commands get registered faster. Can be removed eventually.
test_guild_id = int(os.getenv('GUILD_ID'))

# Change only the no_category default string
help_command = commands.DefaultHelpCommand(
    no_category='Commands',
    width=100
)


description = "Hi! I am a bot to help with creating and loggin inhouses! Please use any of the following commands with a leading ! to use.\nInHouseBot by made by Conner Soule"

bot = discord.Bot(debug_guilds=[test_guild_id])
bot.intents.reactions = True
bot.intents.members = True

inhouse_role = None
main_queue: Queue = None
main_leaderboard = None

# Riot API watcher
watcher = LolWatcher(os.environ.get('Riot_Api_Key'))
my_region = 'na1'


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# Ping
@bot.slash_command(description="Health check. Responds with 'pong'.")
async def ping(ctx):
    await ctx.respond("pong")

# makes match
@commands.has_role("Staff")
@bot.slash_command(description="Staff only command. Makes and starts a match, bypassing the queue.")
async def make_match(ctx, blue_top: discord.Member, red_top: discord.Member, blue_jungle: discord.Member, red_jungle: discord.Member, blue_mid: discord.Member, red_mid: discord.Member, blue_adc: discord.Member, red_adc: discord.Member, blue_support: discord.Member, red_support: discord.Member):
    if main_queue == None:
        await ctx.respond("Please start a queue with /start_queue before making a match")
        return
    res = await ctx.respond("Creating Match...")
    dummy_queued_players = {role_top: [], role_jungle: [], role_mid: [], role_adc: [], role_support: []}
    player = Player(blue_top.id, name=blue_top.display_name,
                    db_handler=db_handler)
    dummy_queued_players[role_top].append(player)
    player = Player(red_top.id, name=red_top.display_name,
                    db_handler=db_handler)
    dummy_queued_players[role_top].append(player)
    player = Player(blue_jungle.id, name=blue_jungle.display_name,
                    db_handler=db_handler)
    dummy_queued_players[role_jungle].append(player)
    player = Player(red_jungle.id, name=red_jungle.display_name,
                    db_handler=db_handler)
    dummy_queued_players[role_jungle].append(player)
    player = Player(blue_mid.id, name=blue_mid.display_name,
                    db_handler=db_handler)
    dummy_queued_players[role_mid].append(player)
    player = Player(red_mid.id, name=red_mid.display_name,
                    db_handler=db_handler)
    dummy_queued_players[role_mid].append(player)
    player = Player(blue_adc.id, name=blue_adc.display_name,
                    db_handler=db_handler)
    dummy_queued_players[role_adc].append(player)
    player = Player(red_adc.id, name=red_adc.display_name,
                    db_handler=db_handler)
    dummy_queued_players[role_adc].append(player)
    player = Player(blue_support.id, name=blue_support.display_name,
                    db_handler=db_handler)
    dummy_queued_players[role_support].append(player)
    player = Player(red_support.id, name=red_support.display_name,
                    db_handler=db_handler)
    dummy_queued_players[role_support].append(player)
    await main_queue.manual_create_match(dummy_queued_players)
    await res.delete_original_message()


# Start Queue
@commands.has_role("Staff")
@bot.slash_command(description="Staff only command. Starts the InHouse Queue in the current channel.")
async def start_queue(ctx):
    res = await ctx.respond("Creating Queue...")
    global main_queue
    main_queue = Queue(ctx=ctx)
    await main_queue.create_queue_message(inhouse_role)
    await res.delete_original_message()

# Test Start
@commands.has_role("Staff")
@bot.slash_command(description="Staff only command. Starts match in the current channel with test values.")
async def test_match(ctx):
    if main_queue == None:
        await ctx.respond("Queue has not been started, nothing to test.")
        return
    res = await ctx.respond("Starting test match...")
    await main_queue.force_start(bot=bot)
    await res.delete_original_message()

# Reset Queue
@commands.has_role("Staff")
@bot.slash_command(description="Staff only command. Resets the InHouse queue, clearing all players.")
async def reset_queue(ctx):
    if main_queue == None:
        await ctx.respond("Queue has not been started, nothing to reset.")
        return
    res = await ctx.respond("Resetting Queue...")
    await ctx.send("Queue has been reset, any active matches will still be tracked. React to the new message to join!")
    await main_queue.reset_queue(inhouse_role)
    await res.delete_original_message()

# Stop Queue
@commands.has_role("Staff")
@bot.slash_command(description="Staff only command. Completely stops the queue.")
async def stop_queue(ctx):
    res = await ctx.respond("Stopping Queue...")
    await main_queue.stop_queue()
    await res.delete_original_message()

# Set Leaderboard Channel
@commands.has_role("Staff")
@bot.slash_command(description="Staff only command. Sets the leaderboard output channel.")
async def set_leaderboard_channel(ctx, channel_name: str):
    channel_id = re.sub("[^0-9]", "", channel_name)
    channel = bot.get_channel(int(channel_id))
    if channel == None:
        await ctx.respond("Channel not found. Send as a #channel.")
        return
    global main_leaderboard
    main_leaderboard = Leaderboard(db_handler=db_handler, channel=channel)
    await ctx.respond("Leaderboard channel updated.")

# Set InHouse role
# TODO: Make role be of type discord.Role
@commands.has_role("Staff")
@bot.slash_command(description="Staff only command. Sets the InHouse role to be pinged when the queue starts. Set as an @Role.")
async def set_inhouse_role(ctx: discord.ApplicationContext, role: discord.Role):
    global inhouse_role
    inhouse_role = role
    res = await ctx.respond("Inhouse role updated")

# Manual leaderboard refresh
@commands.has_role("Staff")
@bot.slash_command(description="Staff only command. Refreshes the leaderboard.")
async def refresh_leaderboard(ctx):
    if main_leaderboard == None:
        await ctx.respond("Leaderboard channel not set")
    else:
        await ctx.respond("Refreshing leaderboard...")
        await main_leaderboard.update_leaderboard()

@commands.has_role("Bot Dev")
@bot.slash_command(description="Bot Dev only command.")
async def add_to_db(ctx, user: discord.Member):
    try: 
        cur = db_handler.get_cursor()
        insert_cmd = f"INSERT INTO players({new_player_db_key}) VALUES ('{user.id}', '{user.name}', '0', '0', '0', '{default_points}')"
        cur.execute(insert_cmd)
        db_handler.complete_transaction(cur)
        await ctx.respond("Done.")
    except Exception as e:
        print(e)
        await ctx.respond("Something bork")

# Swap Players
@commands.has_role("Staff")
@bot.slash_command(description="Staff only comamnd. Swap players in given role for a match. Must be sent in the match thread.")
async def swap_players(ctx, role: str):
    if role.lower() not in roles:
        msg = discord.Embed(
            description="Please enter a valid role: top, jungle, mid, adc, support", color=discord.Color.gold())
        await ctx.respond(embed=msg)
        return
    # must be sent in the thread of the individual game
    #main_queue.active_matches_by_message_id.values()
    matches_to_swap = list(filter(lambda match: match.thread.id == ctx.channel_id, [match for match in main_queue.active_matches_by_message_id.values()]))
    if len(matches_to_swap) != 1:
        msg = discord.Embed(
            description="No active match found in this channel. Send this command in a match thread.", color=discord.Color.gold())
        await ctx.respond(embed=msg)
        return
    
    await matches_to_swap[0].swap_players(role)
    await ctx.respond(f"Swapped {role}")

# Update player history (Add Wins or Losses)
@commands.has_role("Staff")
@bot.slash_command(description="Staff only command. Manually add a win or loss to a given player. Send as @Player ['W' or 'L'].")
async def update_player_history(ctx, user: discord.Member, win_or_loss: str):
    if win_or_loss.lower() not in ['w', 'l']:
        msg = discord.Embed(
            description="Please send update as one of 'W' or 'L'", color=discord.Color.gold())
        await ctx.respond(embed=msg)
        return
    
    user_id = user.id
    # name doesn't matter in this context, we just need to link the id
    player = Player(user_id, name="", db_handler=db_handler)
    player.update_inhouse_standings(win_or_loss)
    await ctx.respond("Player updated.")
    if main_leaderboard == None:
        await ctx.respond("No Leaderboard channel set currently, ask an Admin to set it")
        return
    await main_leaderboard.update_leaderboard()

# MARK: General user Commands
@bot.slash_command(description="Get a player's leaderboard standing. Send as @Player.")
async def standing(ctx: discord.ApplicationContext, user: discord.Member):
    res = await ctx.respond("Getting standing...")
    await db_handler.get_standing(ctx=ctx, requested_user=user)
    await res.delete_original_message()

# Cooldown is once per 5 minutes to prevent spam
@commands.cooldown(rate=1, per=300)
@bot.slash_command(description="Get overall match history for past games")
async def match_history(ctx, count: int):
    if count > 20:
        await ctx.respond("Maximum count is 20.")
        return
    res = await ctx.respond("Getting match history...")
    await db_handler.get_match_history(ctx=ctx, count=count)
    await res.delete_original_message()


@bot.slash_command(description="Opt in or out of soloqueue leaderboard")
async def show_rank(ctx, opt: bool):
    await db_handler.set_show_rank(opt,ctx.author.id)
    await ctx.respond("Updated")

# Cooldown is once per 5 minutes to prevent spam
@commands.cooldown(rate=1, per=300)
@bot.slash_command(description="Shows soloqueue leaderboard")
async def soloqueue(ctx):
    res = await ctx.respond("Getting soloqueue leaderboard...")
    names = await db_handler.get_names()
    player_dict = Soloqueue_Leaderboard()
    for summoner in names:
        try:
            response = watcher.summoner.by_name(my_region,summoner[0]) 
            id = response["id"]
            name = response["name"]
            rank = watcher.league.by_summoner(my_region,id)
            rankStr = ""
            for types in rank:
                if types["queueType"] == solo_queue:
                    tier = types["tier"]
                    playerRank = types["rank"]
                    lp = types["leaguePoints"]
                    break
                else:
                    pass
            if rankStr == "":
                tier = types["tier"]
                playerRank = types["rank"]
            player_dict.add_player(name,tier,playerRank,lp)
        except Exception as e:
            print(e)
    await res.delete_original_message()
    print_msgs = player_dict.get_embbeded()
    for msg in print_msgs:
        await ctx.send(embed=msg)


# Set players nickname with Summoner Name
@bot.slash_command(description="Sets discord nick name. Please enter valid Summoner name")
async def setname(ctx, summoner_name: str):
    if ctx.channel_id != name_assign_channel:
        await ctx.author.send("Can only use /setname in #name-assign. If you need to change your name, please reach out to a Staff member")
        return
    try:
        role = discord.utils.get(ctx.guild.roles, name="Member")
        sum = watcher.summoner.by_name(my_region,summoner_name)
        await ctx.author.add_roles(role)
        await ctx.author.edit(nick=sum["name"])
        await ctx.respond("Welcome " + sum["name"])
    except ApiError as e:
        code = e.response.status_code
        print(e)
        if code == 401 or code == 403:
            await ctx.respond(f"<@&{bot_dev_role}> needs to update riot API key. Please reachout to Staff to fix.")
            return
        await ctx.respond(summoner_name + " is not a summoner name")

@commands.has_role("Staff")
@bot.slash_command(description="casual game modes")
async def casual(ctx: discord.ApplicationContext):
    await ctx.respond("Choose the modes you'd like to play!")
    await ctx.send("Casual games", view=CasualModePicker(timeout=30))

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    # bot reactions to any message are a no-op
    if payload.user_id == bot.user.id:
        return

    # Inhouse Role (if they don't have it)
    if payload.message_id == inhouse_role_assign_message and payload.member.get_role(inhouse_role.id) == None:
        await handle_inhouse_role_reaction(payload=payload)

    # Rest of reactions are queue operations, if one isn't active, short-circuit
    if main_queue == None:
        return
    # Handle Queue reactions
    if payload.message_id == main_queue.queue_message.id:
        # if the emoji isn't one of the role ones we should remove it
        if payload.emoji.id not in all_role_emojis:
            await main_queue.queue_message.clear_reaction(emoji=payload.emoji)
            return
        
        # Otherwise handle the addition
        await handle_queue_reaction(user=payload.member, emoji=payload.emoji, added_reaction=True)

    # handle complete match reactions
    if payload.message_id in main_queue.active_matches_by_message_id.keys():
        # Make sure the rector is a match reporter
        if "Match Reporter" in [role.name for role in payload.member.roles]:
            winner = ''
            if payload.emoji.name == "🟦":
                winner = 'blue'
            elif payload.emoji.name == "🟥":
                winner = 'red'
            else:
                await bot.get_message(payload.message_id).clear_reaction(emoji=payload.emoji)
                return
            
            # remove reactions to prevent extras
            await bot.get_message(payload.message_id).clear_reactions()
            await main_queue.attempt_complete_match(payload.message_id, winner, main_leaderboard=main_leaderboard)
        else:
            print("not a match reporter")
            await bot.get_message(payload.message_id).remove_reaction(emoji=payload.emoji, member=payload.member)

# This handles the bot removing people's reactins from the queue as well
# i.e. if someone attempts to queue up while already in a game this handles the bot removing that reaction gracefully
@bot.event
async def on_raw_reaction_remove(payload):
    # bot reactions to any message are a no-op
    if payload.user_id == bot.user.id:
        return
    if main_queue == None:
        return
    # Handle Queue reaction remove
    if payload.message_id == main_queue.queue_message.id:
        # If a non-role reaction was removed, this function is a no-op
        if payload.emoji.id not in all_role_emojis:
            return
        
        # Otherwise handle the removal
        await handle_queue_reaction(user=payload.user_id, emoji=payload.emoji, added_reaction=False)

# MARK: Util functions

async def handle_inhouse_role_reaction(payload: discord.RawReactionActionEvent):
    try:
        # must get server nickname to match to summoner name
        response = watcher.summoner.by_name(my_region, payload.member.display_name)
        summ_id = response['id']
        leagues = watcher.league.by_summoner(my_region, summ_id)

        tiers = []
        for league in leagues:
            if league['queueType'] in [solo_queue, flex_queue]:
                tiers.append(league['tier'])

        for tier in tiers:
            if tier in ['PLATINUM', 'DIAMOND', 'MASTER', 'GRANDMASTER', 'CHALLENGER']:
                await payload.member.add_roles(inhouse_role)
                return

        # if we got here, they aren't allowed
        # DM them
        await payload.member.send("Sorry! Competitive Inhouses are currently limited to Plat+ Solo/Flex rank.")
        # fetch avoids a caching issue on bot restart
        channel = await bot.fetch_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)
        await msg.remove_reaction(emoji=payload.emoji, member=payload.member)
        return
    except Exception as e:
        print(e)
        await payload.member.send("Check that your discord name has been linked to your summoner name in #name-assign correctly, then try again. If the problem persists, please contact a staff member.")

# NOTE: user can be either an int or a Member object depending on reaction add/remove (int on remove).
# The function handles this on it's own.
async def handle_queue_reaction(user, emoji, added_reaction: bool):
    if added_reaction:
        # stop players from reacting if they're already in a game
        # since we get a list of ids and mush em together we end up with a enested list with one elem, so just pull it out
        match_player_ids = [match.get_all_player_ids() for match in main_queue.active_matches_by_message_id.values()]
        if len(match_player_ids) > 0 and user.id in match_player_ids[0]:
            await main_queue.queue_message.remove_reaction(emoji, member=user)
            return

        # Allow players to react to only one role.
        if user.id in main_queue.all_queued_player_ids():
            await main_queue.queue_message.remove_reaction(emoji, member=user)
            return

    # add player to queue
    # how I wish for switch statements in python :(
    role = ''
    emoji_id = emoji.id
    if emoji_id == top_emoji_id:
        role = role_top
    if emoji_id == jg_emoji_id:
        role = role_jungle
    if emoji_id == mid_emoji_id:
        role = role_mid
    if emoji_id == bot_emoji_id:
        role = role_adc
    if emoji_id == supp_emoji_id:
        role = role_support

    if added_reaction:
        player = Player(user.id, name=user.display_name, db_handler=db_handler)
        main_queue.queued_players[role].append(player)
        await main_queue.attempt_create_match(bot=bot)
    else:
        found_players = list(filter(lambda player: player.id == user, [player for player in main_queue.queued_players[role]]))
        if len(found_players) == 1:
            # If no players match we can assume that the removed reaction was from the bot for a disallowed multi-role queue
            player_to_remove = found_players[0]
            main_queue.queued_players[role].remove(player_to_remove)

print("Bot Starting...")
bot.run(os.environ.get('Discord_Key'))
