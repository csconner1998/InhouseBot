from email import message
from optparse import Values
import discord
import random
from discord.ext import commands
from discord.utils import get
import random
from datetime import datetime
import json
import re
import math
import os
import psycopg2

from inhouse.db_util import DatabaseHandler 
from inhouse.constants import *
from inhouse.command_handlers import match
from inhouse.command_handlers import leaderboard

db_handler = DatabaseHandler(host=os.environ.get('DB_HOST'), db_name=os.environ.get('DB_NAME'), user=os.environ.get('DB_USER'), password=os.environ.get('DB_PASS'))

# Change only the no_category default string
help_command = commands.DefaultHelpCommand(
    no_category = 'Commands',
    width = 100
)
description = "Hi! I am a bot to help with creating and loggin inhouses! Please use any of the following commands with a leading ! to use.\nInHouseBot by made by Conner Soule"
intents = discord.Intents.default()
intents.members = True
intents.reactions = True
bot = commands.Bot(command_prefix='!',help_command = help_command, description = description, intents= intents)
bot.intents.members = True
leaderboardMsgs = []
msgList = []

logChannel = ""
leaderboardChannel = ""
msgID = ""

async def isRole(user,role,message):
    role = discord.utils.find(lambda r: r.name == role, message.guild.roles)
    return role in user.roles

async def checkWinStr(reaction,user):
    cur = db_handler.getCursor()
    cmd = "Select * from active_matches where win_msg_id = '" + str(reaction.message.id) + "'"
    cur.execute(cmd)
    exists = bool(cur.rowcount)
    if not exists:
        return False
    win = ""
    if not isRole(user,"Match Reporter"):
        reaction.remove(user)
        return
    if reaction.emoji == "🟦":
        win = "blue"
    elif reaction.emoji == "🟥":
        win = "red"
    else:
        reaction.remove(user)
        return
    value  = cur.fetchone()
    players = value[1:11]
    activeid = value[0]
    cmd = "INSERT INTO matches(matchid, created,winner) values ('"+str(activeid)+"', '" + str(datetime.now()) + "','"+str(win)+ "') returning matchid"
    cur.execute(cmd)
    matchid = cur.fetchone()[0]
    valueString = ""
    for i in range(len(players)):
        if i % 2 == 0:
            isBlue = "True"
            if win == "blue":
                db_handler.writePlayer("w",players[i])
            else:
                db_handler.writePlayer("l",players[i])
        else:
            isBlue = "False"
            if win == "red":
                db_handler.writePlayer("w",players[i])
            else:
                db_handler.writePlayer("l",players[i])
        role = int(math.floor(i/2))
        valueString += "('" + str(matchid) + "', '" + str(players[i]) + "', '" + isBlue+ "', '" + str(role) + "'),"
    valueString = valueString[:len(valueString) -1]
    cmd = "INSERT INTO matches_players(match_id,player_id,blue,role) values "+valueString
    print(cmd)
    cur.execute(cmd)
    cmd = "delete from active_matches where win_msg_id = '" + str(reaction.message.id) + "'"
    cur.execute(cmd)
    db_handler.completeTransaction(cur)
    await reaction.message.delete()
    await leaderboard.updateLeaderboard(reaction.message.channel, leaderboardMsgs=leaderboardMsgs, leaderboardChannel=leaderboardChannel, db_handler=db_handler)
    
async def checkStart(message):
    count = sum([reaction.count for reaction in message.reactions])
    if count < 15:
        return False
    cur = db_handler.getCursor()
    cmd = "select active_id from active_matches where react_msg_id = '"+str(message.id)+"'"
    cur.execute(cmd)
    exists = bool(cur.rowcount)
    if exists:
        cur.close()
        return ""
    insertStr = "("
    for i in message.reactions:
        if i.emoji.id == top_emoji_id:
            if i.count != 3:
                return ""
            async for user in i.users():
                if user == bot.user:
                    pass
                else:
                    insertStr += "'" + str(user.id) + "',"
        if i.emoji.id == jg_emoji_id:
            if i.count != 3:
                return ""
            async for user in i.users():
                if user == bot.user:
                    pass
                else:
                    insertStr += "'" +  str(user.id) + "',"
        if i.emoji.id == mid_emoji_id:
            if i.count != 3:
                return ""
            async for user in i.users():
                if user == bot.user:
                    pass
                else:
                    insertStr += "'" +  str(user.id)  + "',"
        if i.emoji.id == bot_emoji_id:
            if i.count != 3:
                return ""
            async for user in i.users():
                if user == bot.user:
                    pass
                else:
                    insertStr += "'" +  str(user.id)  + "',"
        if i.emoji.id == supp_emoji_id:
            if i.count != 3:
                return ""
            async for user in i.users():
                if user == bot.user:
                    pass
                else:
                    insertStr += "'" +  str(user.id) + "',"
    insertStr += str(message.id) + ")"
    randomInt = random.randint(0, 1)
    if randomInt == 1:
        topStr= "top1, top2,"
    else:
        topStr="top2, top1,"
    randomInt = random.randint(0, 1)
    if randomInt == 1:
        jungleStr= " jungle1, jungle2,"
    else:
        jungleStr=" jungle2, jungle1,"
    randomInt = random.randint(0, 1)
    if randomInt == 1:
        midStr= " mid1, mid2,"
    else:
        midStr=" mid2, mid1,"
    randomInt = random.randint(0, 1)
    if randomInt == 1:
        adcStr= " adc1, adc2,"
    else:
        adcStr=" adc2, adc1,"
    randomInt = random.randint(0, 1)
    if randomInt == 1:
        supportStr= " support1, support2"
    else:
        supportStr=" support2, support1"
    cmd = f"INSERT INTO active_matches({topStr+jungleStr+midStr+adcStr+supportStr},react_msg_id) values {insertStr} returning active_id"
    cur.execute(cmd)
    value = cur.fetchone()
    db_handler.completeTransaction(cur)
    if value[0] != None:
        return value[0]
    else:
        return ""    
@bot.event
async def on_reaction_remove(reaction, user):
        if reaction.message not in msgList:
            return
        if user == bot.user:
            return
        # await changeMessage(reaction.message,user)

@bot.event
async def on_reaction_add(reaction, user):
    global msgList
    if user == bot.user:
        return 
    if reaction.message not in msgList:
        if await checkWinStr(reaction, user):
            return
        else:
            return
    for reaction2 in reaction.message.reactions:
        async for recuser in reaction2.users():
            if recuser == user and reaction2 != reaction:
                await reaction.remove(user)
                return
    if reaction.count < 2:
        return
    if reaction.emoji.id == top_emoji_id:
        number = reaction.count - 1
        if number > 2:
            await reaction.remove(user)
            return
    elif reaction.emoji.id == jg_emoji_id:
        number = reaction.count - 1
        if number > 2:
            await reaction.remove(user)
            return
    elif reaction.emoji.id == mid_emoji_id:
        number = reaction.count - 1
        if number > 2:
            await reaction.remove(user)
            return
    elif reaction.emoji.id == bot_emoji_id:
        number = reaction.count - 1
        if number > 2:
            await reaction.remove(user)
            return
    elif reaction.emoji.id == supp_emoji_id:
        number = reaction.count - 1
        if number > 2:
            await reaction.remove(user)
            return
    else:
        await reaction.remove(user)
        return
    nameOrNick = user.nick if user.nick else user.name
    db_handler.makePlayer(nameOrNick, user.id)
    startID = await checkStart(reaction.message)
    if startID != "":
        await startGame(reaction.message.channel,startID)

# MARK: Utility commands
@bot.command(help='Just says hi...')
async def test(ctx):
    # print(args)
    await ctx.send("test")
    await ctx.send("Hi!")
    # await ctx.message.delete()

@bot.command(help='STAFF ONLY COMMAND. Used to set leaderboard and logging channel. Input: {leaderboard or log} {#channel}')
@commands.has_role("Staff")
async def setChannel(ctx, *args):
    await ctx.message.delete()
    global logChannel, leaderboardChannel
    if len(args) != 2 or (args[0] != "log" and args[0] != "leaderboard"):
        msg = discord.Embed(
            description="Please send in format !setChannel \{'leaderboard or log'\} \{'#channel'\}", color=discord.Color.gold())
        await ctx.send(embed=msg)
        return
    channelID = re.sub("[^0-9]", "", args[1])
    if channelID == "":
        msg = discord.Embed(
            description="Please send in format !setChannel \{'leaderboard or log'\} \{'#channel'\}", color=discord.Color.gold())
        await ctx.send(embed=msg)
        return
    channel = bot.get_channel(int(channelID))
    if args[0] == "log":
        await channel.send("Now logging here")
        logChannel = channel
    elif args[0] == "leaderboard":
        leaderboardChannel = channel
        await ctx.send(args[1] + " is now the leaderboard channel")

# MARK: Leaderboard commands

@bot.command(help='Used to check your SP and W/L ratio. Input {@user}')
async def soulrushStanding(ctx, *args):
    await leaderboard.getLeaderboardStanding(bot, ctx, args, db_handler)

# MARK: Match commands

@bot.command(help='Starts a match lobby')
async def start(ctx):
    await match.startMatchLobby(ctx, msgList=msgList)

@bot.command(help="Used to swap members in created game. Input: {game id} {Role}")
@commands.has_role("Staff")
async def swap(ctx, *args):
    await match.swapPlayers(ctx, args, db_handler=db_handler)

@bot.command(help='Used to display match history. Limit 10.')
async def matchhistory(ctx):
    match.getMatchHistory(ctx, db_handler=db_handler)

@bot.command(help='Lists active matches.')
async def activeMatches(ctx):
    match.listActiveMatches(ctx, db_handler=db_handler)

async def startGame(ctx, id):
    await match.printMatch(ctx,id,db_handler=db_handler)
    cur = db_handler.getCursor()
    whoWon = discord.Embed(description="Who Won?", color=discord.Color.gold())
    wonStr = await ctx.send(embed=whoWon)
    cmd = "UPDATE active_matches SET win_msg_id = '" + str(wonStr.id) + "' where active_id = '" + str(id) + "'"
    cur.execute(cmd)
    db_handler.completeTransaction(cur)
    await wonStr.add_reaction("🟦")
    await wonStr.add_reaction("🟥")

bot.run(os.environ.get('Discord_Key'))