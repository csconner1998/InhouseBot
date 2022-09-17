from urllib.request import DataHandler
import discord
import inhouse.db_util

class CoinManager(object):
    def __init__(self, db_handler: inhouse.db_util.DatabaseHandler) -> None:
        self.db_handler = db_handler

    def update_member_coins(self, member: discord.Member, coin_amount: int):
        self.create_member_entry_if_necessary(member=member)
        cmd = f"UPDATE coins SET coin_count = coin_count + {coin_amount} WHERE discord_id = '{member.id}' "
        cur = self.db_handler.get_cursor()
        cur.execute(cmd)
        self.db_handler.complete_transaction(cursor=cur)

    def get_member_coins(self, member: discord.Member):
        self.create_member_entry_if_necessary(member=member)
        cmd = f"SELECT coin_count from coins WHERE discord_id = '{member.id}'"
        cur = self.db_handler.get_cursor()
        cur.execute(cmd)
        coin_amount = cur.fetchone()
        cur.close()
        return coin_amount[0]

    def create_member_entry_if_necessary(self, member: discord.Member):  
        cmd = f"SELECT discord_id FROM coins WHERE discord_id = {member.id}"
        cur = self.db_handler.get_cursor()
        cur.execute(cmd)
        existing_player_id = cur.fetchone()

        if existing_player_id == None:
            insert_cmd = f"INSERT INTO coins(discord_id, coin_count) VALUES ('{member.id}', '0')"
            cur.execute(insert_cmd)
        self.db_handler.complete_transaction(cursor=cur)

        
