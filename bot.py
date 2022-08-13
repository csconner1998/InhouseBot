from concurrent.futures import thread
from optparse import Values
import queue
import discord
from discord.ext import commands
import random
from dotenv import load_dotenv
import re
import os
from inhouse.command_handlers.player import Player

from inhouse.db_util import DatabaseHandler 
from inhouse.constants import *
from inhouse.command_handlers.queue import Queue
from inhouse.command_handlers.leaderboard import Leaderboard
#from inhouse.command_handlers.match import match
#from inhouse.command_handlers.leaderboard import leaderboard

print("done imports")

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
load_dotenv()
db_handler = DatabaseHandler(host=os.environ.get('DB_HOST'), db_name=os.environ.get('DB_NAME'), user=os.environ.get('DB_USER'), password=os.environ.get('DB_PASS'))
print("done load env")

# Change only the no_category default string
help_command = commands.DefaultHelpCommand(
    no_category = 'Commands',
    width = 100
)
description = "Hi! I am a bot to help with creating and loggin inhouses! Please use any of the following commands with a leading ! to use.\nInHouseBot by made by Conner Soule"
test_guild_id = int(os.getenv('GUILD_ID'))

bot = discord.Bot(debug_guilds=[test_guild_id])
bot.intents.reactions = True
bot.intents.members = True

inhouse_role_id = None

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# Ping
@bot.slash_command(guild_ids=[test_guild_id])
async def ping(ctx):
    await ctx.respond("pong")
# TODO: match history command

# TODO change all Bot Dev to Staff
# Start Queue
@commands.has_role("Bot Dev")
@bot.slash_command(guild_ids=[test_guild_id])
async def start_queue(ctx):
    # TODO: change this respond to like an image banner or smth nice
    await ctx.respond("Creating Queue...")
    global main_queue
    main_queue = Queue(ctx=ctx)
    await main_queue.create_queue_message(inhouse_role_id)

# Clear Queue
@commands.has_role("Bot Dev")
@bot.slash_command(guild_ids=[test_guild_id])
async def clear_queue(ctx):
    await main_queue.clear_queue()

# Set Leaderboard Channel
@commands.has_role("Bot Dev")
@bot.slash_command(guild_ids=[test_guild_id])
async def set_leaderboard_channel(ctx, channel_name: str):
    channel_id = re.sub("[^0-9]", "", channel_name)
    channel = bot.get_channel(int(channel_id))
    if channel == None:
        await ctx.respond("Channel not found")
        return
    global main_leaderboard
    main_leaderboard = Leaderboard(db_handler=db_handler, channel=channel)
    await ctx.respond("Leaderboard channel updated")

# Set inhouse role
@commands.has_role("Bot Dev")
@bot.slash_command(guild_ids=[test_guild_id])
async def set_inhouse_role(ctx, role: str):
    global inhouse_role_id
    inhouse_role_id = role
    await ctx.respond("Inhouse role updated")

# Swap Players
@commands.has_role("Bot Dev")
@bot.slash_command(guild_ids=[test_guild_id])
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
@commands.has_role("Bot Dev")
@bot.slash_command(guild_ids=[test_guild_id])
async def update_player_history(ctx, user: str, win_or_loss: str):
    if win_or_loss.lower() not in ['w', 'l']:
        msg = discord.Embed(
            description="Please send update as one of 'W' or 'L'", color=discord.Color.gold())
        await ctx.respond(embed=msg)
        return
    
    # trim the tag crap off the user ID
    user_id = re.sub("[^0-9]", "", user)
    # name doesn't matter in this context, we just need to link the id
    player = Player(user_id, name="", db_handler=db_handler)
    player.update_player_in_db(win_or_loss)
    await ctx.respond("Player updated.")
    if main_leaderboard == None:
        await ctx.respond("No leaderboard channel set currently")
        return
    await main_leaderboard.update_leaderboard()

@bot.event
async def on_raw_reaction_add(payload):
    # bot reactions to any message are a no-op
    if payload.user_id == bot.user.id:
        print("reaction from bot, ignoring...")
        return

    # Handle Queue reactions
    if payload.message_id == main_queue.queue_message.id:
        print("reaction to queue")
        print(payload)
        # if the emoji isn't one of the role ones we should remove it
        if payload.emoji.id not in all_role_emojis:
            print(f"non-role reaction id {payload.emoji} added, removing...")
            await main_queue.queue_message.clear_reaction(emoji=payload.emoji)
            return
        
        # Otherwise handle the addition
        await handle_queue_reaction(user=payload.member, emoji_id=payload.emoji.id, added_reaction=True)

    # handle complete match reactions
    if payload.message_id in main_queue.active_matches_by_message_id.keys() and main_leaderboard != None:
        await main_queue.attempt_complete_match(payload.message_id, '', main_leaderboard=main_leaderboard)

# This handles the bot removing people's reactins from the queue as well
# i.e. if someone attempts to queue up while already in a game this handles the bot removing that reaction gracefully
@bot.event
async def on_raw_reaction_remove(payload):
    print(payload)
    # bot reactions to any message are a no-op
    if payload.user_id == bot.user.id:
        print("reaction from bot, ignoring...")
        return

    # Handle Queue reaction remove
    if payload.message_id == main_queue.queue_message.id:
        print("reaction to queue")
        # If a non-role reaction was removed, this function is a no-op
        if payload.emoji.id not in all_role_emojis:
            print("non-role reaction removed, ignoring...")
            return
        
        # Otherwise handle the removal
        await handle_queue_reaction(user=payload.user_id, emoji_id=payload.emoji.id, added_reaction=False)

# NOTE: user can be either an int or a Member object depending on reaction add/remove (int on remove).
# The function handles this on it's own.
async def handle_queue_reaction(user, emoji_id, added_reaction: bool):
    # Slightly jank condition chain
    # stop players from reacting if they're already in a game
    if not type(user) is int and user.id in [player_id for player_id in [match.get_all_player_ids() for match in main_queue.active_matches_by_message_id.values()]]:
        print("player reacting is already in an active match, removing reaction and returning...")
        await main_queue.queue_message.remove_reaction(emoji_id, member=user)
        return

    # TODO: limit to 1 reaction on queue message per player once done testing
    # add player to queue
    role = ''
    if emoji_id == top_emoji_id:
        print("top player")
        role = role_top
    if emoji_id == jg_emoji_id:
        print("jg player")
        role = role_jungle
    if emoji_id == mid_emoji_id:
        print("mid player")
        role = role_mid
    if emoji_id == bot_emoji_id:
        print("adc player")
        role = role_adc
    if emoji_id == supp_emoji_id:
        print("supp player")
        role = role_support

    if added_reaction:
        player = Player(user.id, name=user.display_name, db_handler=db_handler)
        print(f"adding player {player}")
        main_queue.queued_players[role].append(player)
        await main_queue.attempt_create_match()
    else:
        player_to_remove = list(filter(lambda player: player.id == user, [player for player in main_queue.queued_players[role]]))[0]
        print(f"removing player {player_to_remove}")
        main_queue.queued_players[role].remove(player_to_remove)

bot.run(os.environ.get('Discord_Key'))