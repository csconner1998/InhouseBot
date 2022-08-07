import discord
import re
from inhouse.constants import soulrush_id

class Leaderboard(object):
    def __init__(self, db_handler, channel: discord.TextChannel) -> None:
        self.channel: discord.TextChannel = channel
        self.current_leaderboard_messages = []
        self.db_handler = db_handler

    async def update_leaderboard(self):
        cur = self.db_handler.getCursor()
        cmd = "SELECT * FROM players ORDER BY SP DESC, win DESC"
        cur.execute(cmd)
        players = cur.fetchall()
        new_msgs_to_send = []
        for idx, player in enumerate(players):
            # create a new message if we've reached 10 players
            if idx % 10 == 0:
                msg = discord.Embed(color=discord.Color.gold())
                name_str = ""
                sp_str = ""
                winloss_str = ""
            if idx == 0:
                msg.title = ":trophy: Standings :trophy:"
                win = player[2]
                loss = player[3]
                ratio = player[4]
                SP = player[5]
                name = player[1]
                name_str += f"{str(idx+1)}. {name}\n"
                sp_str += f"** {str(SP)} SP** \n"
                winloss_str += f"{str(win)}/{str(loss)} - {str(ratio)}%\n"
            if idx % 10 == 9:
                msg.add_field(name="Summoner", value=name_str, inline=True)
                msg.add_field(name="Soulrush Points", value=sp_str, inline=True)
                msg.add_field(name="W/L", value=winloss_str, inline=True)
                new_msgs_to_send.append(msg)

        self.channel.delete_messages(self.current_leaderboard_messages)
        sent_messages = []
        for message in new_msgs_to_send:
            sentMsg = await self.channel.send(embed=message)
            sent_messages.append(sentMsg)
        self.current_leaderboard_messages = sent_messages