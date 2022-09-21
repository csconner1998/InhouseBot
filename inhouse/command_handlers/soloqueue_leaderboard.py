from gc import callbacks
from tkinter import Label
import discord
from discord.utils import get
from discord.ext import tasks
from operator import itemgetter
import inhouse.constants
import inhouse.global_objects
import time
from datetime import datetime
import inhouse.db_util

class Soloqueue_Leaderboard(object):
    def __init__(self, db_handler: inhouse.db_util.DatabaseHandler, channel: discord.TextChannel, region: str) -> None:
        self.clearDict()
        self.channel = channel
        self.db_handler = db_handler
        self.my_region = region
        self.tierMap = {"IRON" : 0, "BRONZE" : 1, "SILVER" : 2, "GOLD" : 3, "PLATINUM" : 4, "DIAMOND" : 5, "MASTER" : 6, "GRANDMASTER" : 6, "CHALLENGER" : 6}
        self.divMap = {"IV" : 0, "III" : 1, "II": 2, "I" : 3}
    
    def clearDict(self):
        self.player_list=[]

    def add_player(self,name,tier,rank,lp,last_lp):
        calc_lp = self.calc_lp(tier,rank,lp)
        player_obj = (name, tier, rank, lp, calc_lp,last_lp)
        self.player_list.append(player_obj)

    def get_embbeded(self, emojiList):
        msg_list = []
        i = 0
        name_string = ""
        rank_string = ""
        num_string = ""
        msg = None
        challengerEmoji = get(emojiList, name="Challenger")
        grandmasterEmoji = get(emojiList, name="Grandmaster")
        masterEmoji = get(emojiList, name="Master")
        diamondEmoji = get(emojiList, name="Diamond")
        platinumEmoji = get(emojiList, name="Platinum")
        goldEmoji = get(emojiList, name="Gold")
        silverEmoji = get(emojiList, name="Silver")
        bronzeEmoji = get(emojiList, name="Bronze")
        ironEmoji = get(emojiList, name="Iron")
        unratedEmoji = get(emojiList, name="Unranked")
        greenTriangleEmoji = get(emojiList, name="GreenTriangle")
        redTriangleEmoji = get(emojiList, name="RedTriangle")
        emojiMap = {"UNRANKED" : unratedEmoji, "IRON" : ironEmoji, "BRONZE" : bronzeEmoji, "SILVER" : silverEmoji, "GOLD" : goldEmoji, "PLATINUM" : platinumEmoji, "DIAMOND" : diamondEmoji, "MASTER" : masterEmoji, "GRANDMASTER" : grandmasterEmoji, "CHALLENGER" : challengerEmoji}
        for name, tier, rank, lp, calc_lp, last_lp in sorted(self.player_list, key = itemgetter(4), reverse=True):
            if last_lp != None:
                lp_diff = calc_lp - last_lp
                if lp_diff < 0:
                    lp_diff = f"{redTriangleEmoji}{(0-lp_diff)}"
                else:
                    lp_diff = f"{greenTriangleEmoji}{lp_diff}"
            else:
                lp_diff = f"{greenTriangleEmoji} 0"
            name_string += f"{emojiMap[tier]} {name}\n"
            rank_string += f"{tier} {rank} {lp} LP\n"     
            num_string += f"{self.num_ranked_past_week(name)} ({lp_diff} LP)\n"

            i += 1
            if i % 10 == 0:
                msg = discord.Embed(color=discord.Color.blue())
                if i == 10:
                    msg.title = ":trophy: **Soloqueue Standings** :trophy:"
                msg.add_field(name="Summoner", value=name_string, inline=True)
                msg.add_field(name="Rank", value=rank_string, inline=True)
                msg.add_field(name="Games in Past Week", value=num_string, inline=True)
                msg_list.append(msg)
                rank_string = ""
                name_string = ""
                num_string = ""
        if i != 0:
            msg = discord.Embed(color=discord.Color.blue())
            msg.add_field(name="Summoner", value=name_string, inline=True)
            msg.add_field(name="Rank", value=rank_string, inline=True)
            msg.add_field(name="Games in Past Week", value=num_string, inline=True)
            msg_list.append(msg)
        return msg_list
        
    @tasks.loop(hours=inhouse.constants.solo_queue_leaderboard_loop_timer)
    async def make(self, emojiList):
        print("Making soloqueue leaderboard")
        self.clearDict()
        names = await self.db_handler.get_names()
        for summoner in names:
            try:
                response = inhouse.global_objects.watcher.summoner.by_name(self.my_region,summoner[0]) 
                id = response["id"]
                name = response["name"]
                rank = inhouse.global_objects.watcher.league.by_summoner(self.my_region,id)
                playerRank = ""
                lp = 0
                last_lp = summoner[2]
                tier = ""
                for types in rank:
                    if types["queueType"] == inhouse.constants.solo_queue:
                        tier = types["tier"]
                        playerRank = types["rank"]
                        lp = types["leaguePoints"]
                        break
                    else:
                        pass
                if playerRank == "":
                    playerRank == "UNRANKED"
                    tier = "UNRANKED"
                    lp = 0
                self.add_player(name,tier,playerRank,lp,last_lp)
                # if weekday is 0 (monday) and the hour of now is 8 (8am) reset the weeks LP
                if datetime.now().weekday() == 0 and datetime.now().hour == 8:
                    await self.db_handler.set_week_lp(summoner[1],self.calc_lp(tier=tier,div=playerRank,lp=lp))
            except Exception as e:
                print(e)
        async for message in self.channel.history(limit=50):
            await message.delete()
        msgs = self.get_embbeded(emojiList)
        for msg in msgs:
            await self.channel.send(embed=msg)
        

        await self.channel.send(view=JoinButtons(self.db_handler))

    def num_ranked_past_week(self, name: str):
        try:
            response = inhouse.global_objects.watcher.summoner.by_name(self.my_region,summoner_name=name) 
            puuid = response['puuid']
            # subtract number of seconds in a week to get a week ago epoch time
            week_ago = int(time.time() - inhouse.constants.seconds_in_week)
            #queue type 420 is "solo queue" according to riot API documentation (lol)
            response = inhouse.global_objects.watcher.match.matchlist_by_puuid(self.my_region,puuid=puuid,start_time=week_ago,queue=420,count=100)
            return len(response)
        except Exception as e:
                print(e)

    def calc_lp(self,tier,div,lp):
        if tier == "UNRANKED":
            return 0
        return (100 * self.divMap[div]) + (400 * self.tierMap[tier]) + int(lp)

class JoinButtons(discord.ui.View): # Create a class called MyView that subclasses discord.ui.View
    def __init__(self, db_handler: inhouse.db_util.DatabaseHandler):
        super().__init__()
        self.db_handler = db_handler

    @discord.ui.button(label="Show Rank", style=discord.ButtonStyle.blurple)
    async def show_rank(self, button, interaction):
        print("Add to DB")
        await self.db_handler.set_show_rank(interaction.user.id,interaction.user.display_name,True)
        await interaction.response.send_message("Added. You will now show up on next leaderboard reset.", ephemeral=True)

    @discord.ui.button(label="Hide Rank", style=discord.ButtonStyle.red)
    async def not_show_rank(self, button, interaction):
        print("Remove from DB")
        await self.db_handler.set_show_rank(interaction.user.id,interaction.user.display_name,False)
        await interaction.response.send_message("Removed. You will no longer show up on next leaderboard reset.", ephemeral=True)
