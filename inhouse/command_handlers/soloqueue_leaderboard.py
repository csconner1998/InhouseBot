import discord
from discord.utils import get
from discord.ext import tasks
from operator import itemgetter
import inhouse.constants
import inhouse.global_objects
import time

class Soloqueue_Leaderboard(object):
    def __init__(self, db_handler, channel: discord.TextChannel, region: str) -> None:
        self.clearDicts()
        self.channel = channel
        self.db_handler = db_handler
        self.my_region = region
    
    def clearDicts(self):
        self.challenger_dict = {"I":[]}
        self.grandmaster_dict = {"I":[]}
        self.master_dict = {"I":[]}
        self.diamond_dict = {"I":[],"II":[],"III":[],"IV":[]}
        self.platinum_dict = {"I":[],"II":[],"III":[],"IV":[]}
        self.gold_dict = {"I":[],"II":[],"III":[],"IV":[]}
        self.silver_dict = {"I":[],"II":[],"III":[],"IV":[]}
        self.bronze_dict = {"I":[],"II":[],"III":[],"IV":[]}
        self.iron_dict = {"I":[],"II":[],"III":[],"IV":[]}
        self.unranked_dict = []

    def add_player(self,name,tier,rank,lp):
        if tier == "CHALLENGER":
            self.challenger_dict[rank].append((name, lp))
        elif tier == "GRANDMASTER":
            self.grandmaster_dict[rank].append((name, lp))
        elif tier == "MASTER":
            self.master_dict[rank].append((name, lp))
        elif tier == "DIAMOND":
            self.diamond_dict[rank].append((name, lp))
        elif tier == "PLATINUM":
            self.platinum_dict[rank].append((name, lp))
        elif tier == "GOLD":
            self.gold_dict[rank].append((name, lp))
        elif tier == "SILVER":
            self.silver_dict[rank].append((name, lp))
        elif tier == "BRONZE":
            self.bronze_dict[rank].append((name, lp))
        elif tier == "IRON":
            self.iron_dict[rank].append((name, lp))
        else:
            self.unranked_dict.append((name, lp))
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
        for rank in self.challenger_dict:
            for player in sorted(self.challenger_dict[rank], key = itemgetter(1), reverse=True):
                name_string += f"{challengerEmoji} {player[0]}\n"
                rank_string += f"Challenger {rank} {str(player[1])} LP\n"     
                num_string += f"{self.num_ranked_past_week(player[0])}\n"

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
        for rank in self.grandmaster_dict:
            for player in sorted(self.grandmaster_dict[rank], key = itemgetter(1), reverse=True):
                name_string += f"{grandmasterEmoji} {player[0]}\n"
                rank_string += f"Grandmaster {rank} {str(player[1])} LP\n"                
                num_string += f"{self.num_ranked_past_week(player[0])}\n"
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
        for rank in self.master_dict:
            for player in sorted(self.master_dict[rank], key = itemgetter(1), reverse=True):
                name_string += f"{masterEmoji} {player[0]}\n"
                rank_string += f"Master {rank} {str(player[1])} LP\n"
                num_string += f"{self.num_ranked_past_week(player[0])}\n"
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
        for rank in self.diamond_dict:
            for player in sorted(self.diamond_dict[rank], key = itemgetter(1), reverse=True):
                name_string += f"{diamondEmoji} {player[0]}\n"
                rank_string += f"Diamond {rank} {str(player[1])} LP\n"                
                num_string += f"{self.num_ranked_past_week(player[0])}\n"
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
        for rank in self.platinum_dict:
            for player in sorted(self.platinum_dict[rank], key = itemgetter(1), reverse=True):
                name_string += f"{platinumEmoji} {player[0]}\n"
                rank_string += f"Platinum {rank} {str(player[1])} LP\n"                
                num_string += f"{self.num_ranked_past_week(player[0])}\n"
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
        for rank in self.gold_dict:
            for player in sorted(self.gold_dict[rank], key = itemgetter(1), reverse=True):
                name_string += f"{goldEmoji} {player[0]}\n"
                rank_string += f"Gold {rank} {str(player[1])} LP\n"                
                num_string += f"{self.num_ranked_past_week(player[0])}\n"
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
        for rank in self.silver_dict:
            for player in sorted(self.silver_dict[rank], key = itemgetter(1), reverse=True):
                name_string += f"{silverEmoji} {player[0]}\n"
                rank_string += f"Silver {rank} {str(player[1])} LP\n"                
                num_string += f"{self.num_ranked_past_week(player[0])}\n"
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
        for rank in self.bronze_dict:
            for player in sorted(self.bronze_dict[rank], key = itemgetter(1), reverse=True):
                name_string += f"{bronzeEmoji} {player[0]}\n"
                rank_string += f"Bronze {rank} {str(player[1])} LP\n"                
                num_string += f"{self.num_ranked_past_week(player[0])}\n"
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
        for rank in self.iron_dict:
            for player in sorted(self.iron_dict[rank], key = itemgetter(1), reverse=True):
                name_string += f"{ironEmoji} {player[0]}\n"
                rank_string += f"Iron {rank} {str(player[1])} LP\n"                
                num_string += f"{self.num_ranked_past_week(player[0])}\n"
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
        for player in self.unranked_dict:
            name_string += f"{unratedEmoji} {player[0]}\n"
            rank_string += f"Unranked\n"
            num_string += f"{self.num_ranked_past_week(player[0])}\n"
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
        self.clearDicts()
        names = await self.db_handler.get_names()
        for summoner in names:
            try:
                response = inhouse.global_objects.watcher.summoner.by_name(self.my_region,summoner[0]) 
                id = response["id"]
                name = response["name"]
                if name == "Jayms":
                    print("here")
                rank = inhouse.global_objects.watcher.league.by_summoner(self.my_region,id)
                playerRank = ""
                lp = 0
                tier = ""
                for types in rank:
                    if types["queueType"] == inhouse.constants.solo_queue:
                        tier = types["tier"]
                        playerRank = types["rank"]
                        lp = types["leaguePoints"]
                        break
                    else:
                        pass
                self.add_player(name,tier,playerRank,lp)
            except Exception as e:
                print(e)
        async for message in self.channel.history(limit=50):
            await message.delete()
        msgs = self.get_embbeded(emojiList)
        for msg in msgs:
            await self.channel.send(embed=msg)
        await self.channel.send("Please use /show_rank to join leaderboard")
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
        