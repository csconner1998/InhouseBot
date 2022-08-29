import discord

class Leaderboard(object):
    def __init__(self, db_handler, channel: discord.TextChannel) -> None:
        self.channel: discord.TextChannel = channel
        self.current_leaderboard_messages = []
        self.db_handler = db_handler

    async def update_leaderboard(self):
        cur = self.db_handler.get_cursor()
        # this limit will probably never be hit but good to keep around
        cmd = "SELECT * FROM players ORDER BY SP DESC, win DESC LIMIT 100"
        cur.execute(cmd)
        players = cur.fetchall()
        cur.close()
        new_msgs_to_send = []
        
        for idx, player in enumerate(players):
            if idx % 10 == 0:
                # create a new message if we've reached 10 players
                msg = discord.Embed(color=discord.Color.gold())
                player_names = ""
                player_points = ""
                player_winlosses = ""
                
            if idx == 0:
                # Set overall title
                msg.title = ":trophy: **STANDINGS** :trophy:"

            win = player[2]
            loss = player[3]
            if win + loss == 0:
                ratio = 0
            else:
                ratio = int(win/(win+loss) * 100)
            SP = player[4]
            name = player[1]

            player_names += f"{str(idx+1)}. {name}\n"
            player_points += f"** {str(SP)} SP** \n"
            player_winlosses += f"{str(win)}/{str(loss)} - {str(ratio)}%\n"

            if idx % 10 == 9:
                # populate message
                msg.add_field(name="Summoner", value=player_names, inline=True)
                msg.add_field(name="Soulrush Points", value=player_points, inline=True)
                msg.add_field(name="W/L", value=player_winlosses, inline=True)
                new_msgs_to_send.append(msg)
        
        # Handle overflow if not evenly divisible by 10
        if idx % 10 != 9:
            msg.add_field(name="Summoner", value=player_names, inline=True)
            msg.add_field(name="Soulrush Points", value=player_points, inline=True)
            msg.add_field(name="W/L", value=player_winlosses, inline=True)
            new_msgs_to_send.append(msg)

        # clear previous messages in channel if this is a new leaderboard instance
        if self.current_leaderboard_messages == []:
            async for message in self.channel.history(limit=50):
                await message.delete()
        else:
            await self.channel.delete_messages(self.current_leaderboard_messages)
        sent_messages = []
        for message in new_msgs_to_send:
            sentMsg = await self.channel.send(embed=message)
            sent_messages.append(sentMsg)
        self.current_leaderboard_messages = sent_messages
