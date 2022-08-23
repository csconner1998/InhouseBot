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

    def update_inhouse_standings(self, WinLoss):
        self.update_name()
        cur = self.db_handler.get_cursor()
        cmd = f"SELECT win, loss,sp FROM players WHERE id ='{str(self.id)}'"
        cur.execute(cmd)
        value = cur.fetchone()
        winNum = int(value[0])
        losNum = int(value[1])
        spNum = int(value[2])
        if str.lower(WinLoss) == "w":
            winNum += 1
            spNum += win_points
        else:
            losNum += 1
            spNum -= loss_points
            if spNum < 0:
                spNum = 0
        ratioStr = int(100 * (winNum / (winNum + losNum)))
        cmd = f"UPDATE players SET win = '{str(winNum)}', loss = '{str(losNum)}', sp = '{str(spNum)}', ratio = '{str(ratioStr)}' where id ='{str(self.id)}';"
        cur.execute(cmd)
        self.db_handler.complete_transaction(cur)
    
    def update_name(self):
        cur = self.db_handler.get_cursor()
        cmd = f"UPDATE players SET name = '{self.name}' where id ='{str(self.id)}'"
        cur.execute(cmd)
        self.db_handler.complete_transaction(cursor=cur)

    def update_coins(self, amount: int):
        cur = self.db_handler.get_cursor()
    