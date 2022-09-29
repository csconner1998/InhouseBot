from riotwatcher import LolWatcher, ApiError
from inhouse.command_handlers.coin_manager import CoinManager
from inhouse.command_handlers.queue import *

class RolesHolder():
    def __init__(self, competitive_inhouse: discord.Role, casual_inhouse: discord.Role, normals: discord.Role, flex: discord.Role, aram: discord.Role, rgm: discord.Role) -> None:
        self.competitive_inhouse = competitive_inhouse
        self.casual_inhouse = casual_inhouse
        self.normals = normals
        self.flex = flex
        self.aram = aram
        self.rgm = rgm

casual_queue: Queue = None
casual_queue_aram: AramQueue = None
server_roles: RolesHolder = None
main_queue: Queue = None
watcher = LolWatcher(os.environ.get('Riot_Api_Key'))
coin_manager: CoinManager = None
main_leaderboard: Leaderboard = None
solo_queue_leaderboard: Leaderboard = None