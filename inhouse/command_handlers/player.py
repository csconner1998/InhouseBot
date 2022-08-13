import discord
from inhouse.constants import *
from inhouse.db_util import DatabaseHandler
import re

class Player(object):
    """
    Represents a player, holding data for:
    - discord ID (which is also our DB ID for players)
    - user name (from discord name/nickname)
    """
    def __init__(self, id, name: str, db_handler: DatabaseHandler) -> None:
        self.name = name
        self.id = id
        self.db_handler = db_handler

    def update_player_in_db(self, WinLoss):
        cur = self.db_handler.get_cursor()
        cmd = f"SELECT win, loss,sp FROM players WHERE id ='{str(self.id)}'"
        cur.execute(cmd)
        value = cur.fetchone()
        winNum = int(value[0])
        losNum = int(value[1])
        spNum = int(value[2])
        # TODO: return win/loss nums to 1 from 0
        if str.lower(WinLoss) == "w":
            winNum += 0
            spNum += win_points
        else:
            losNum += 0
            spNum -= loss_points
            if spNum < 0:
                spNum = 0
        ratioStr = int(100 * (winNum / (winNum + losNum)))
        cmd = f"UPDATE players SET win = '{str(winNum)}', loss = '{str(losNum)}', sp = '{str(spNum)}', ratio = '{str(ratioStr)}' where id ='{str(self.id)}';"
        cur.execute(cmd)
        self.db_handler.complete_transaction(cur)
    
    @staticmethod
    async def get_standing(bot, ctx, *args, db_handler):
        """
        bot- the discord bot
        ctx- context to send the message in
        args- args to command, should be an @tag for user
        db_handler- db handler
        """
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
        cur = db_handler.get_cursor()
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
        db_handler.complete_transaction(cur)
