import enum

# MARK: IDs
top_emoji_id = 1003021609239588875
jg_emoji_id = 1003014949196546150
mid_emoji_id = 1003024543494963220
bot_emoji_id = 1003022277631283240
supp_emoji_id = 1003027602698670282
all_role_emojis = [top_emoji_id, jg_emoji_id, mid_emoji_id, bot_emoji_id, supp_emoji_id]

soulrush_bot_id = 197473689263013898

# MARK: ROLES
role_top = 'top'
role_jungle = 'jungle'
role_mid = 'mid'
role_adc = 'adc'
role_support = 'support'
roles = [role_top, role_jungle, role_mid, role_adc, role_support]

# MARK: DB Keys
all_roles_db_key = "top1, jungle1, mid1, adc1, support1, top2, jungle2, mid2, adc2, support2"
new_player_db_key = "id, name, win, loss, ratio, sp"

# MARK: Misc
default_points = 500
# TODO: return to 15/12
win_points = 0
loss_points = 0
