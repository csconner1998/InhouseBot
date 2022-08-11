import discord
import math
from inhouse.constants import *

"""
Holds all utility functions related to match operations
"""

async def startMatchLobby(ctx, msgList):
    await ctx.message.delete()
    msgStr = f"```GAME```Top: <:Top:{top_emoji_id}>\nJungle: <:jungle:{jg_emoji_id}>\nMid: <:Mid:{mid_emoji_id}>\nAdc: <:Bottom:{bot_emoji_id}>\nSupport: <:Support:{supp_emoji_id}>"
    msg = discord.Embed(
    description=msgStr, color=discord.Color.gold())
    message = await ctx.send(embed=msg)
    msgList.append(message)
    await message.add_reaction(f"<:Top:{top_emoji_id}>")
    await message.add_reaction(f"<:jungle:{jg_emoji_id}>")
    await message.add_reaction(f"<:Mid:{mid_emoji_id}>")
    await message.add_reaction(f"<:Bottom:{bot_emoji_id}>")
    await message.add_reaction(f"<:Support:{supp_emoji_id}>")

async def getMatchHistory(ctx, db_handler):
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

async def swapPlayers(ctx, *args, db_handler):
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
    await printMatch(ctx, str(gameNum), db_handler=db_handler)

async def printMatch(ctx, matchID, db_handler):
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

async def listActiveMatches(ctx, db_handler):
    await ctx.message.delete()
    cur = db_handler.getCursor()
    cmd = "SELECT active_id FROM active_matches;"
    cur.execute(cmd)
    matchIDs = cur.fetchall()
    for matchid in matchIDs:
        await printMatch(ctx,str(matchid[0]), db_handler=db_handler)