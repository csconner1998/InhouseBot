import discord
from discord.utils import get
from discord.ext import tasks
from operator import itemgetter
import inhouse.constants
import inhouse.global_objects
import time
from datetime import datetime
import inhouse.db_util
from ratelimit import limits, sleep_and_retry

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

    def add_player(self,name,tier,rank,lp,last_lp,num_ranked):
        calc_lp = self.calc_lp(tier,rank,lp)
        player_obj = (name, tier, rank, lp, calc_lp,last_lp,num_ranked)
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
        for name, tier, rank, lp, calc_lp, last_lp, num_ranked in sorted(self.player_list, key = itemgetter(4), reverse=True):
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
            num_string += f"{num_ranked} ({lp_diff} LP)\n"

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
        if i % 10 != 0:
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
                puuid = summoner[3]
                id = summoner[4]
                name = summoner[0]
                if puuid == None or id == None:
                    raise Exception(name + " doesn't have puuid")
                rank, num_ranked = self.api_calls(id,puuid)
                time.sleep(0.1)
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
                self.add_player(name,tier,playerRank,lp,last_lp,num_ranked)
                # if weekday is 0 (monday) and the hour of now is 8 (8am) reset the weeks LP
                if datetime.now().weekday() == 0 and datetime.now().hour == 8:
                    await self.db_handler.set_week_lp(summoner[1],self.calc_lp(tier=tier,div=playerRank,lp=lp))

                    # Top 3 get coins at start of every week (100, 50, 25)
                    coins_to_grant = inhouse.constants.coins_for_soloq_leader
                    for name, _, _, _, _, _ in sorted(self.player_list, key = itemgetter(4), reverse=True)[:3]:
                        member = self.channel.guild.get_member_named(name)
                        if member == None:
                            print(f"Did not grant coins to {name}")
                            continue
                        inhouse.global_objects.coin_manager.update_member_coins(member=member, coin_amount=coins_to_grant)
                        coins_to_grant /= 2

            except Exception as e:
                print(e)

        async for message in self.channel.history(limit=50):
            await message.delete()
        msgs = self.get_embbeded(emojiList)
        for msg in msgs:
            await self.channel.send(embed=msg)
        await self.channel.send(view=JoinButtons(self.db_handler))

    def num_ranked_past_week(self, puuid):
        try:
            # subtract number of seconds in a week to get a week ago epoch time
            week_ago = int(time.time() - inhouse.constants.seconds_in_week)
            #queue type 420 is "solo queue" according to riot API documentation (lol)
            response = inhouse.global_objects.watcher.match.matchlist_by_puuid(self.my_region,puuid=puuid,start_time=week_ago,queue=420,count=100)
            return len(response)
        except Exception as e:
                print(e)

    # rate limits are 20 every second and 100 every 2 min, since we are calling API twice its 10 every second and 100 every 2 minutes
    @limits(calls=10, period=1)
    @limits(calls=100, period=inhouse.constants.seconds_in_two_min)
    @sleep_and_retry
    def api_calls(self, sum_id, puuid):
        try:
            rank = inhouse.global_objects.watcher.league.by_summoner(self.my_region,sum_id)
            # subtract number of seconds in a week to get a week ago epoch time
            week_ago = int(time.time() - inhouse.constants.seconds_in_week)
            #queue type 420 is "solo queue" according to riot API documentation (lol)
            response = inhouse.global_objects.watcher.match.matchlist_by_puuid(self.my_region,puuid=puuid,start_time=week_ago,queue=420,count=100)
            return rank, len(response)
        except Exception as e:
                print(e)
        
    def calc_lp(self,tier,div,lp):
        if tier == "UNRANKED":
            return 0
        return (100 * self.divMap[div]) + (400 * self.tierMap[tier]) + int(lp)

class JoinButtons(discord.ui.View): # Create a class called MyView that subclasses discord.ui.View
    def __init__(self, db_handler: inhouse.db_util.DatabaseHandler):
        super().__init__(timeout=None)
        self.db_handler = db_handler
        self.my_region = "na1"

    @discord.ui.button(label="Show Rank", style=discord.ButtonStyle.blurple)
    async def show_rank(self, button, interaction):
        print("Add to DB")
        try:
            response = inhouse.global_objects.watcher.summoner.by_name(self.my_region,interaction.user.display_name)
            id = response["id"]
            puuid = response['puuid']
            await self.db_handler.set_show_rank(interaction.user.id,interaction.user.display_name, True, id, puuid)
            await interaction.response.send_message("Added. You will now show up on next leaderboard reset.", ephemeral=True)
        except Exception as e:
            print(e)
            await interaction.response.send_message("Your display name isn't an IGN. Please update your nickname or connect Staff", ephemeral=True)


    @discord.ui.button(label="Hide Rank", style=discord.ButtonStyle.red)
    async def not_show_rank(self, button, interaction):
        print("Remove from Soloq Leaderboard")
        await self.db_handler.set_show_rank(interaction.user.id,interaction.user.display_name,False)
        await interaction.response.send_message("Removed. You will no longer show up on next leaderboard reset.", ephemeral=True)
