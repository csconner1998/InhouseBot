from optparse import Values
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

# intents = discord.Intents.default()
# intents.members = True
# intents.reactions = True
bot = discord.Bot(debug_guilds=[test_guild_id])
bot.intents.reactions = True
bot.intents.members = True


#bot = commands.Bot(command_prefix='!')
#bot.intents.members = True
leaderboardMsgs = []
msgList = []

logChannel = ""
leaderboardChannel = ""
msgID = ""


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# TODO: remove IDs from repo
@bot.slash_command(guild_ids=[test_guild_id])
async def ping(ctx):
    await ctx.respond("pong")

# TODO change to staff
@commands.has_role("Bot Dev")
@bot.slash_command(guild_ids=[test_guild_id])
async def start_queue(ctx):
    global main_queue
    main_queue = Queue(ctx=ctx)
    await main_queue.create_queue_message()
    await ctx.respond("Queue Started")

@commands.has_role("Bot Dev")
@bot.slash_command(guild_ids=[test_guild_id])
async def clear_queue(ctx):
    await main_queue.clear_queue()

@bot.slash_command(guild_ids=[test_guild_id])
async def set_leaderboard_channel(ctx, channel_name: str):
    # TODO: error handling/messages
    channel_id = re.sub("[^0-9]", "", channel_name)
    print(channel_id)
    channel = bot.get_channel(int(channel_id))
    global main_leaderboard
    main_leaderboard = Leaderboard(db_handler=db_handler, channel=channel)
    await ctx.respond("Leaderboard channel updated")

@bot.event
async def on_raw_reaction_add(payload):
    # ignore bot reactions
    if payload.user_id == bot.user.id:
        print("reaction from bot, ignoring...")
        return

    # TODO: we can keep a list of valid things to handle so that we don't do this for every reaction in the server
    # Handle Queue reactions
    if payload.message_id == main_queue.queue_message.id:
        print("reaction to queue")
        await handle_queue_reaction(user=payload.member, emoji_id=payload.emoji.id)

    # handle complete match reactions
    if main_leaderboard != None:
        await main_queue.attempt_complete_match(payload.message_id, '', main_leaderboard=main_leaderboard)

async def handle_queue_reaction(user, emoji_id):
    # add player to queue
    player = Player(user.id, name=user.display_name, db_handler=db_handler)
    if emoji_id == top_emoji_id:
        print("top player")
        main_queue.queued_players['top'].append(player)
    if emoji_id == jg_emoji_id:
        print("jg player")
        main_queue.queued_players['jungle'].append(player)
    if emoji_id == mid_emoji_id:
        print("mid player")
        main_queue.queued_players['mid'].append(player)
    if emoji_id == bot_emoji_id:
        print("adc player")
        main_queue.queued_players['adc'].append(player)
    if emoji_id == supp_emoji_id:
        print("supp player")
        main_queue.queued_players['support'].append(player)

    await main_queue.attempt_create_match()

bot.run(os.environ.get('Discord_Key'))

# async def checkWinStr(reaction,user):
#     cur = db_handler.get_cursor()
#     cmd = "Select * from active_matches where win_msg_id = '" + str(reaction.message.id) + "'"
#     cur.execute(cmd)
#     exists = bool(cur.rowcount)
#     if not exists:
#         return False
#     win = ""
#     if reaction.emoji == "🟦":
#         win = "blue"
#     elif reaction.emoji == "🟥":
#         win = "red"
#     else:
#         reaction.remove(user)
#         return
#     value  = cur.fetchone()
#     players = value[1:11]
#     activeid = value[0]
#     cmd = "INSERT INTO matches(matchid, created,winner) values ('"+str(activeid)+"', '" + str(datetime.now()) + "','"+str(win)+ "') returning matchid"
#     cur.execute(cmd)
#     matchid = cur.fetchone()[0]
#     valueString = ""
#     for i in range(len(players)):
#         if i % 2 == 0:
#             isBlue = "True"
#             if win == "blue":
#                 db_handler.writePlayer("w",players[i])
#             else:
#                 db_handler.writePlayer("l",players[i])
#         else:
#             isBlue = "False"
#             if win == "red":
#                 db_handler.writePlayer("w",players[i])
#             else:
#                 db_handler.writePlayer("l",players[i])
#         role = int(math.floor(i/2))
#         valueString += "('" + str(matchid) + "', '" + str(players[i]) + "', '" + isBlue+ "', '" + str(role) + "'),"
#     valueString = valueString[:len(valueString) -1]
#     cmd = "INSERT INTO matches_players(match_id,player_id,blue,role) values "+valueString
#     print(cmd)
#     cur.execute(cmd)
#     cmd = "delete from active_matches where win_msg_id = '" + str(reaction.message.id) + "'"
#     cur.execute(cmd)
#     db_handler.complete_transaction(cur)
#     await reaction.message.delete()
#     await leaderboard.updateLeaderboard(reaction.message.channel, leaderboardMsgs=leaderboardMsgs, leaderboardChannel=leaderboardChannel, db_handler=db_handler)
    
# async def checkStart(message):
#     if len(message.reactions) < 12:
#         return
#     cur = db_handler.get_cursor()
#     cmd = "select active_id from active_matches where react_msg_id = '"+str(message.id)+"'"
#     cur.execute(cmd)
#     exists = bool(cur.rowcount)
#     if exists:
#         cur.close()
#         return  
#     insertStr = "("
#     for i in message.reactions:
#         if i.emoji.id == top_emoji_id:
#             if i.count != 3:
#                 return ""
#             async for user in i.users():
#                 if user == bot.user:
#                     pass
#                 else:
#                     insertStr += "'" + str(user.id) + "',"
#         if i.emoji.id == jg_emoji_id:
#             if i.count != 3:
#                 return ""
#             async for user in i.users():
#                 if user == bot.user:
#                     pass
#                 else:
#                     insertStr += "'" +  str(user.id) + "',"
#         if i.emoji.id == mid_emoji_id:
#             if i.count != 3:
#                 return ""
#             async for user in i.users():
#                 if user == bot.user:
#                     pass
#                 else:
#                     insertStr += "'" +  str(user.id)  + "',"
#         if i.emoji.id == bot_emoji_id:
#             if i.count != 3:
#                 return ""
#             async for user in i.users():
#                 if user == bot.user:
#                     pass
#                 else:
#                     insertStr += "'" +  str(user.id)  + "',"
#         if i.emoji.id == supp_emoji_id:
#             if i.count != 3:
#                 return ""
#             async for user in i.users():
#                 if user == bot.user:
#                     pass
#                 else:
#                     insertStr += "'" +  str(user.id) + "',"
#     insertStr += str(message.id) + ")"
#     randomInt = random.randint(0, 1)
#     if randomInt == 1:
#         topStr= "top1, top2,"
#     else:
#         topStr="top2, top1,"
#     randomInt = random.randint(0, 1)
#     if randomInt == 1:
#         jungleStr= " jungle1, jungle2,"
#     else:
#         jungleStr=" jungle2, jungle1,"
#     randomInt = random.randint(0, 1)
#     if randomInt == 1:
#         midStr= " mid1, mid2,"
#     else:
#         midStr=" mid2, mid1,"
#     randomInt = random.randint(0, 1)
#     if randomInt == 1:
#         adcStr= " adc1, adc2,"
#     else:
#         adcStr=" adc2, adc1,"
#     randomInt = random.randint(0, 1)
#     if randomInt == 1:
#         supportStr= " support1, support2"
#     else:
#         supportStr=" support2, support1"
#     cmd = f"INSERT INTO active_matches({topStr+jungleStr+midStr+adcStr+supportStr},react_msg_id) values {insertStr} returning active_id"
#     cur.execute(cmd)
#     value = cur.fetchone()
#     db_handler.complete_transaction(cur)
#     if value[0] != None:
#         return value[0]
#     else:
#         return ""    
# @bot.event
# async def on_reaction_remove(reaction, user):
#         if reaction.message not in msgList:
#             return
#         if user == bot.user:
#             return
#         # await changeMessage(reaction.message,user)

# @bot.event
# async def on_reaction_add(reaction, user):
#     global msgList
#     if user == bot.user:
#         return 
#     if reaction.message not in msgList:
#         if await checkWinStr(reaction, user):
#             return
#         else:
#             return
#     for reaction2 in reaction.message.reactions:
#         async for recuser in reaction2.users():
#             if recuser == user and reaction2 != reaction:
#                 await reaction.remove(user)
#                 return
#     if reaction.count < 2:
#         return
#     if reaction.emoji.id == top_emoji_id:
#         number = reaction.count - 1
#         if number > 2:
#             await reaction.remove(user)
#             return
#     elif reaction.emoji.id == jg_emoji_id:
#         number = reaction.count - 1
#         if number > 2:
#             await reaction.remove(user)
#             return
#     elif reaction.emoji.id == mid_emoji_id:
#         number = reaction.count - 1
#         if number > 2:
#             await reaction.remove(user)
#             return
#     elif reaction.emoji.id == bot_emoji_id:
#         number = reaction.count - 1
#         if number > 2:
#             await reaction.remove(user)
#             return
#     elif reaction.emoji.id == supp_emoji_id:
#         number = reaction.count - 1
#         if number > 2:
#             await reaction.remove(user)
#             return
#     else:
#         await reaction.remove(user)
#         return
#     nameOrNick = user.nick if user.nick else user.name
#     db_handler.makePlayer(nameOrNick, user.id)
#     startID = await checkStart(reaction.message)
#     if startID != "":
#         await startGame(reaction.message.channel,startID)

# MARK: Utility commands

#@bot.command(help='Just says hi...')
# @bot.command()
# async def test(ctx):
#     print("in tests")
#     # print(args)
#     await ctx.send("test")
#     await ctx.send("Hi!")
    # await ctx.message.delete()

# @bot.command(help='STAFF ONLY COMMAND. Used to set leaderboard and logging channel. Input: {leaderboard or log} {#channel}')
# @commands.has_role("Staff")
# async def setChannel(ctx, *args):
#     await ctx.message.delete()
#     global logChannel, leaderboardChannel
#     if len(args) != 2 or (args[0] != "log" and args[0] != "leaderboard"):
#         msg = discord.Embed(
#             description="Please send in format !setChannel \{'leaderboard or log'\} \{'#channel'\}", color=discord.Color.gold())
#         await ctx.send(embed=msg)
#         return
#     channelID = re.sub("[^0-9]", "", args[1])
#     if channelID == "":
#         msg = discord.Embed(
#             description="Please send in format !setChannel \{'leaderboard or log'\} \{'#channel'\}", color=discord.Color.gold())
#         await ctx.send(embed=msg)
#         return
#     channel = bot.get_channel(int(channelID))
#     if args[0] == "log":
#         await channel.send("Now logging here")
#         logChannel = channel
#     elif args[0] == "leaderboard":
#         leaderboardChannel = channel
#         await ctx.send(args[1] + " is now the leaderboard channel")

# MARK: WIP queue Commands



# @bot.command(help="set leaderboard channel")
# async def setLeaderboardChannel(ctx, *args):
#     # TODO: error handling/messages
#     await ctx.message.delete()
#     channel_id = re.sub("[^0-9]", "", args[1])
#     channel = bot.get_channel(int(channel_id))
#     global main_leaderboard
#     main_leaderboard = leaderboard.Leaderboard(db_handler=db_handler, channel=channel)
# # MARK: Leaderboard commands

# @bot.command(help='Used to check your SP and W/L ratio. Input {@user}')
# async def soulrushStanding(ctx, *args):
#     await leaderboard.getLeaderboardStanding(bot, ctx, args, db_handler)

# MARK: Match commands

# @bot.command(help='Starts a match lobby')
# async def start(ctx):
#     await match.startMatchLobby(ctx, msgList=msgList)

# @bot.command(help="Used to swap members in created game. Input: {game id} {Role}")
# @commands.has_role("Staff")
# async def swap(ctx, *args):
#     await match.swapPlayers(ctx, args, db_handler=db_handler)

# @bot.command(help='Used to display match history. Limit 10.')
# async def matchhistory(ctx):
#     match.getMatchHistory(ctx, db_handler=db_handler)

# @bot.command(help='Lists active matches.')
# async def activeMatches(ctx):
#     match.listActiveMatches(ctx, db_handler=db_handler)

# async def startGame(ctx, id):
#     await match.printMatch(ctx,id,db_handler=db_handler)
#     cur = db_handler.get_cursor()
#     whoWon = discord.Embed(description="Who Won?", color=discord.Color.gold())
#     wonStr = await ctx.send(embed=whoWon)
#     cmd = "UPDATE active_matches SET win_msg_id = '" + str(wonStr.id) + "' where active_id = '" + str(id) + "'"
#     cur.execute(cmd)
#     db_handler.complete_transaction(cur)
#     await wonStr.add_reaction("🟦")
#     await wonStr.add_reaction("🟥")

# print("trying to run...")
# bot.run(os.environ.get('Discord_Key'))
