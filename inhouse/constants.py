import discord
# TODO: all of these should be a config yml/json in the future.

# MARK: IDs
top_emoji_id = 1003021609239588875
jg_emoji_id = 1003014949196546150
mid_emoji_id = 1003024543494963220
bot_emoji_id = 1003022277631283240
supp_emoji_id = 1003027602698670282
all_role_emojis = [top_emoji_id, jg_emoji_id, mid_emoji_id, bot_emoji_id, supp_emoji_id]

aram_emoji_id = 1009563351946371102

soulrush_bot_id = 197473689263013898

name_assign_channel = 1009553154305695816
bot_spam_channel = 1021446812177006682
bot_dev_role = 1001367008086081547

inhouse_role_assign_message = 1013201403633750086

voice_channels = [(997533706346573926, 998335001340944386),(998335056332455979, 998335026469027930),(998335076775514152,998335040964542524)]

# MARK: ROLES
role_top = 'top'
role_jungle = 'jungle'
role_mid = 'mid'
role_adc = 'adc'
role_support = 'support'
roles = [role_top, role_jungle, role_mid, role_adc, role_support]
role_str_to_db_id = {role_top: 0, role_jungle: 1, role_mid: 2, role_adc: 3, role_support: 4}

# MARK: DB Keys
all_roles_db_key = "top1, jungle1, mid1, adc1, support1, top2, jungle2, mid2, adc2, support2"
new_player_db_key = "id, name, win, loss, sp"

# MARK: League Constants
solo_queue = "RANKED_SOLO_5x5"
flex_queue = "RANKED_FLEX_SR"
region = 'na1'

# MARK: Misc
default_points = 500
win_points = 15
loss_points = 12
move_to_channel_delay = 30

# 6 hours in seconds
casual_game_timeout = 21600
seconds_in_week = 604800
solo_queue_leaderboard_loop_timer = 12
seconds_in_two_min = 120

# MARK: Wonkoin stuff
# TODO: really need a config file soon

coins_for_casual_game = 5
coins_for_competitive_inhouse_win = 20
coins_for_competitive_inhouse_loss = coins_for_competitive_inhouse_win / 2
coins_for_casual_inhouse_win = 10
coins_for_casual_inhouse_loss = coins_for_casual_inhouse_win / 2
coins_for_soloq_leader = 100

cost_for_embed_message = 20
