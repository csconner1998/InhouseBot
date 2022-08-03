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

from lib.db_util import DatabaseHandler 
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
roles = ["top", "mid", "jungle", "adc", "support"]
leaderboardMsgs = []
msgList = []

logChannel = ""
leaderboardChannel = ""
msgID = ""





async def checkWinStr(reaction,user):
    cur = db_handler.getCursor()
    cmd = "Select * from active_matches where win_msg_id = '" + str(reaction.message.id) + "'"
    cur.execute(cmd)
    exists = bool(cur.rowcount)
    if not exists:
        return False
    win = ""
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
    await leaderboard(reaction.message.channel)
    
async def checkStart(message):
    cur = db_handler.getCursor()
    cmd = "select active_id from active_matches where react_msg_id = '"+str(message.id)+"'"
    cur.execute(cmd)
    exists = bool(cur.rowcount)
    if exists:
        cur.close()
        return  
    insertStr = "("
    for i in message.reactions:
        if i.emoji.id == 1003021609239588875:
            if i.count != 3:
                return ""
            async for user in i.users():
                if user == bot.user:
                    pass
                else:
                    insertStr += "'" + str(user.id) + "',"
        if i.emoji.id == 1003014949196546150:
            if i.count != 3:
                return ""
            async for user in i.users():
                if user == bot.user:
                    pass
                else:
                    insertStr += "'" +  str(user.id) + "',"
        if i.emoji.id == 1003024543494963220:
            if i.count != 3:
                return ""
            async for user in i.users():
                if user == bot.user:
                    pass
                else:
                    insertStr += "'" +  str(user.id)  + "',"
        if i.emoji.id == 1003022277631283240:
            if i.count != 3:
                return ""
            async for user in i.users():
                if user == bot.user:
                    pass
                else:
                    insertStr += "'" +  str(user.id)  + "',"
        if i.emoji.id == 1003027602698670282:
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
    cmd = "INSERT INTO active_matches("+topStr+jungleStr+midStr+adcStr+supportStr+",react_msg_id) values " + insertStr + " returning active_id"
    cur.execute(cmd)
    value = cur.fetchone()
    db_handler.completeTransaction(cur)
    return value[0]
    


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
    if reaction.emoji.id == 1003021609239588875:
        number = reaction.count - 1
        if number > 2:
            await reaction.remove(user)
            return
    elif reaction.emoji.id == 1003014949196546150:
        number = reaction.count - 1
        if number > 2:
            await reaction.remove(user)
            return
    elif reaction.emoji.id == 1003024543494963220:
        number = reaction.count - 1
        if number > 2:
            await reaction.remove(user)
            return
    elif reaction.emoji.id == 1003022277631283240:
        number = reaction.count - 1
        if number > 2:
            await reaction.remove(user)
            return
    elif reaction.emoji.id == 1003027602698670282:
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

    
    
@bot.command(help='Just says hi...')
async def start(ctx):
    global msgList
    await ctx.message.delete()
    msgStr = "```GAME```Top: <:Top:1003021609239588875>\nJungle: <:jungle:1003014949196546150>\nMid: <:Mid:1003024543494963220>\nAdc: <:Bottom:1003022277631283240>\nSupport: <:Support:1003027602698670282>"
    msg = discord.Embed(
    description=msgStr, color=discord.Color.gold())
    message = await ctx.send(embed=msg)
    msgList.append(message)
    await message.add_reaction("<:Top:1003021609239588875>")
    await message.add_reaction("<:jungle:1003014949196546150>")
    await message.add_reaction("<:Mid:1003024543494963220>")
    await message.add_reaction("<:Bottom:1003022277631283240>")
    await message.add_reaction("<:Support:1003027602698670282>")


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


@bot.command(help='Used to check your SP and W/L ratio. Input {@user}')
async def opgg(ctx, *args):
    await ctx.message.delete()
    if len(args) != 1:
        msg = discord.Embed(
            description="Please send in format !winLoss \{'name'\}", color=discord.Color.gold())
        await ctx.send(embed=msg)
        return
    player = args[0]
    if not (str.startswith(player, '<@') and str.endswith(player, '>')):
        msg = discord.Embed(
            description=str(player) + " is a valid @. Please send in format !add \{@name\} \{role\}", color=discord.Color.gold())
        await ctx.send(embed=msg)
        return
    playerID = int(re.sub("[^0-9]", "", player))
    player = await bot.fetch_user(playerID)
    if not player:
        msg = discord.Embed(
            description=args[0] + " is a valid @. Please send in format !add \{@name\} \{role\}", color=discord.Color.gold())
        await ctx.send(embed=msg)
        return
    db_handler.makePlayer(player.name,playerID)
    cur = db_handler.getCursor()
    cmd = "SELECT name, win, loss, ratio, sp FROM players WHERE id ='" + str(playerID) + "'"
    cur.execute(cmd)
    value = cur.fetchone()
    win = value[1]
    loss = value[2]
    ratio = value[3]
    SP = value[4]
    name = value[0]
    msg = discord.Embed(color=discord.Color.gold())
    nameStr = name + "\n"
    SPstr = "**" + str(SP) + " SP** " + "\n"
    Ratstr = str(win) + "/" + str(loss) + " - " +str(ratio) + "% " + "\n"
    msg.add_field(name="Summoner", value=nameStr, inline=True)
    msg.add_field(name="Soulrush Points", value=SPstr, inline=True)
    msg.add_field(name="W/L", value=Ratstr, inline=True)
    await ctx.send(embed=msg)
    db_handler.completeTransaction(cur)



@bot.command(help="Used to swap members in created game. Input: {game id} {Role}")
@commands.has_role("Staff")
async def swap(ctx, *args):
    global roles
    await ctx.message.delete()
    if len(args) != 2:
        msg = discord.Embed(
            description="Please send in format a !swap \{game id\} {role\}", color=discord.Color.gold())
        await ctx.send(embed=msg)
        return
    pickedRole = str.lower(str.strip(args[1]))
    if pickedRole not in roles:
        msg = discord.Embed(
            description="Please send in format a !swap \{game id\} \{role\}", color=discord.Color.gold())
        await ctx.send(embed=msg)
        return
    gameNum = ''
    try:
        gameNum = int(args[0])
    except ValueError:
        msg = discord.Embed(
            description=args[0] + " isn't a number. Please send in format a !join \{game id\}\{role\}", color=discord.Color.gold())
        await ctx.send(embed=msg)
        return
    cur = db_handler.getCursor()
    cmd = "Update active_matches set "+pickedRole+"1 = "+pickedRole+"2, "+pickedRole+"2 = "+pickedRole+"1 where active_id = " + str(gameNum)
    print(cmd)
    cur.execute(cmd)
    db_handler.completeTransaction(cur)
    await printMatch(ctx, str(gameNum))

async def leaderboard(ctx):
    global leaderboardMsgs
    if leaderboardChannel == "" and ctx == "" and not (ctx != "" and ctx.author.id != 197473689263013898):
        return
    cur = db_handler.getCursor()
    cmd = "select * from players order by SP DESC, win DESC"
    cur.execute(cmd)
    players = cur.fetchall()
    index = 0
    msgList = []
    for player in players:
        if index % 10 == 0:
            msg = discord.Embed(color=discord.Color.gold())
            nameStr = ""
            SPstr = ""
            Ratstr = ""
        if index == 0:
            msg.title = ":trophy: Standings :trophy:"
        win = player[2]
        loss = player[3]
        ratio = player[4]
        SP = player[5]
        name = player[1]
        # format BETTER
        nameStr += str(index+1) + ". " + name + "\n"
        SPstr += "**" + str(SP) + " SP** " + "\n"
        Ratstr += str(win) + "/" + str(loss) + " - " +str(ratio) + "% " + "\n"
        # totalStr+=str(index) + ". " + name + " **" + str(SP) + " SP** " + str(ratio) + "% " + str(win) + "/" + str(loss) + "\n"
        if index % 10 == 9:
            msg.add_field(name="Summoner", value=nameStr, inline=True)
            msg.add_field(name="Soulrush Points", value=SPstr, inline=True)
            msg.add_field(name="W/L", value=Ratstr, inline=True)
            msgList.append(msg)
        index += 1
    if index % 15 != 9:
        msg.add_field(name="Summoner", value=nameStr, inline=True)
        msg.add_field(name="Soulrush Points", value=SPstr, inline=True)
        msg.add_field(name="W/L", value=Ratstr, inline=True)
        msgList.append(msg)
    for i in leaderboardMsgs:
        await i.delete()
    leaderboardMsgs = []
    for message in msgList:
        if leaderboardChannel != "":
            sentMsg = await leaderboardChannel.send(embed=message)
        elif ctx != "":
            sentMsg = await ctx.send(embed=message)
        leaderboardMsgs.append(sentMsg)
    cur.close()

@bot.command(help='Used to display match history. Limit 10.')
async def matchhistory(ctx):
    await ctx.message.delete()
    cur = db_handler.getCursor()
    cmd = "SELECT match_id, name, blue, winner FROM matches_players INNER JOIN players ON matches_players.player_id = players.id inner join matches on matches_players.match_id = matches.matchid ORDER BY matches.matchid DESC, blue ASC limit 100;"
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

@bot.command(help='Lists active matches ')
async def activeMatches(ctx):
    await ctx.message.delete()
    cur = db_handler.getCursor()
    cmd = "SELECT active_id FROM active_matches;"
    cur.execute(cmd)
    matchIDs = cur.fetchall()
    for matchid in matchIDs:
        await printMatch(ctx,str(matchid[0]))

async def printMatch(ctx, matchID):
    try:
        gameNum = int(matchID)
    except ValueError:
        msg = discord.Embed(
            description=matchID + " isn't a number. Please send in format a !printMatch {game id}", color=discord.Color.gold())
        await ctx.send(embed=msg)
        return    
    redString = ""
    blueString = ""
    cur = db_handler.getCursor()
    cmd = "SELECT top1, top2, jungle1,jungle2,mid1,mid2,adc1,adc2,support1,support2 FROM active_matches WHERE active_id ='" + str(matchID) + "'"
    cur.execute(cmd)
    mappingIndex = {0:"top", 1:"jungle", 2:"mid", 3:"adc", 4:"support"}
    exists = bool(cur.rowcount)
    if not exists:
        msg = discord.Embed(
            description=matchID + " isn't an active match. Use !activeMatches to get game IDs", color=discord.Color.gold())
        await ctx.send(embed=msg)
        return  
    value = cur.fetchone()
    iter = 0
    teamR = []
    teamB = []
    for i in value:
        cmd = "SELECT name FROM players WHERE id ='" + str(i) + "'"
        cur.execute(cmd)
        value2 = cur.fetchone() 
        if iter % 2 == 0:
            blueString += mappingIndex[int(math.floor(iter/2))] + ": " +  value2[0] + "\n"
            teamB.append((i,value2[0]))
        else:
            redString += mappingIndex[int(math.floor(iter/2))] + ": " +  value2[0] + "\n"
            teamR.append((i,value2[0]))
        iter += 1
    msg = discord.Embed(description = "```Game "+ str(matchID) +"```",color=discord.Color.gold())
    msg.add_field(name="Blue Team", value=blueString, inline=True)
    msg.add_field(name="Red Team", value=redString, inline=True)
    await ctx.send(embed=msg)
    cur.close()
    # await ctx.channel.send(embed=redEmb)

async def startGame(ctx, id):
    await printMatch(ctx,id)
    cur = db_handler.getCursor()
    whoWon = discord.Embed(description="Who Won?", color=discord.Color.gold())
    wonStr = await ctx.send(embed=whoWon)
    cmd = "UPDATE active_matches SET win_msg_id = '" + str(wonStr.id) + "' where active_id = '" + str(id) + "'"
    cur.execute(cmd)
    db_handler.completeTransaction(cur)
    await wonStr.add_reaction("🟦")
    await wonStr.add_reaction("🟥")

bot.run(os.environ.get('Discord_Key'))