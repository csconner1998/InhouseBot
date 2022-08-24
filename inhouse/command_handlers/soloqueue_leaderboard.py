import discord
from operator import itemgetter

class Soloqueue_Leaderboard(object):
    def __init__(self) -> None:
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
    def get_embbeded(self):
        msg_list = []
        i = 0
        total_string = "```Soloqueue Leaderboard```\n"
        msg = None
        for rank in self.challenger_dict:
            for player in sorted(self.challenger_dict[rank], key = itemgetter(1), reverse=True):
                total_string += f"{player[0]}: Challenger {rank} {str(player[1])} LP\n"                
                i += 1
                if i == 10:
                    i = 0
                    msg = discord.Embed(description=total_string, color=discord.Color.gold())
                    msg_list.append(msg)
                    total_string = ""
        for rank in self.grandmaster_dict:
            for player in sorted(self.grandmaster_dict[rank], key = itemgetter(1), reverse=True):
                total_string += f"{player[0]}: Grandmaster {rank} {str(player[1])} LP\n"                
                i += 1
                if i == 10:
                    i = 0
                    msg = discord.Embed(description=total_string, color=discord.Color.gold())
                    msg_list.append(msg)
                    total_string = ""
        for rank in self.master_dict:
            for player in sorted(self.master_dict[rank], key = itemgetter(1), reverse=True):
                total_string += player[0] + ": " + "Master " + rank + " " + str(player[1]) + "LP\n"
                i += 1
                if i == 10:
                    i = 0
                    msg = discord.Embed(description=total_string, color=discord.Color.gold())
                    msg_list.append(msg)
                    total_string = ""
        for rank in self.diamond_dict:
            for player in sorted(self.diamond_dict[rank], key = itemgetter(1), reverse=True):
                total_string += f"{player[0]}: Diamond {rank} {str(player[1])} LP\n"                
                i += 1
                if i == 10:
                    i = 0
                    msg = discord.Embed(description=total_string, color=discord.Color.gold())
                    msg_list.append(msg)
                    total_string = ""
        for rank in self.platinum_dict:
            for player in sorted(self.platinum_dict[rank], key = itemgetter(1), reverse=True):
                total_string += f"{player[0]}: Platinum {rank} {str(player[1])} LP\n"                
                i += 1
                if i == 10:
                    i = 0
                    msg = discord.Embed(description=total_string, color=discord.Color.gold())
                    msg_list.append(msg)
                    total_string = ""
        for rank in self.gold_dict:
            for player in sorted(self.gold_dict[rank], key = itemgetter(1), reverse=True):
                total_string += f"{player[0]}: Gold {rank} {str(player[1])} LP\n"                
                i += 1
                if i == 10:
                    i = 0
                    msg = discord.Embed(description=total_string, color=discord.Color.gold())
                    msg_list.append(msg)
                    total_string = ""
        for rank in self.silver_dict:
            for player in sorted(self.silver_dict[rank], key = itemgetter(1), reverse=True):
                total_string += f"{player[0]}: Silver {rank} {str(player[1])} LP\n"                
                i += 1
                if i == 10:
                    i = 0
                    msg = discord.Embed(description=total_string, color=discord.Color.gold())
                    msg_list.append(msg)
                    total_string = ""
        for rank in self.bronze_dict:
            for player in sorted(self.bronze_dict[rank], key = itemgetter(1), reverse=True):
                total_string += f"{player[0]}: Bronze {rank} {str(player[1])} LP\n"                
                i += 1
                if i == 10:
                    i = 0
                    msg = discord.Embed(description=total_string, color=discord.Color.gold())
                    msg_list.append(msg)
                    total_string = ""
        for rank in self.iron_dict:
            for player in sorted(self.iron_dict[rank], key = itemgetter(1), reverse=True):
                total_string += f"{player[0]}: Iron {rank} {str(player[1])} LP\n"                
                i += 1
                if i == 10:
                    i = 0
                    msg = discord.Embed(description=total_string, color=discord.Color.gold())
                    msg_list.append(msg)
                    total_string = ""
        for player in self.unranked_dict:
            total_string += f"{player[0]}: Unranked"
            i += 1
            if i == 10:
                i = 0
                msg = discord.Embed(description=total_string, color=discord.Color.gold())
                msg_list.append(msg)
                total_string = ""
        if i != 0:
            msg = discord.Embed(description=total_string, color=discord.Color.gold())
            msg_list.append(msg)
        return msg_list