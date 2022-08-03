import discord
import re
from inhouse.constants import soulrush_id

async def getLeaderboardStanding(bot, ctx, *args, db_handler):
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

async def updateLeaderboard(ctx, leaderboardMsgs, leaderboardChannel, db_handler):
    if leaderboardChannel == "" and ctx == "" and not (ctx != "" and ctx.author.id != soulrush_id):
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
    if index % 10 != 9:
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