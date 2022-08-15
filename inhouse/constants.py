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
role_str_to_db_id = {role_top: 0, role_jungle: 1, role_mid: 2, role_adc: 3, role_support: 4}

# MARK: DB Keys
all_roles_db_key = "top1, jungle1, mid1, adc1, support1, top2, jungle2, mid2, adc2, support2"
new_player_db_key = "id, name, win, loss, ratio, sp"

# MARK: Misc
default_points = 500
win_points = 15
loss_points = 12

# MARK: Logging
# TODO: this should default to Error on deployed system.
# Create a custom logger
def make_logger():
    logger = logging.getLogger(__name__)

    # Create handlers
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.DEBUG)

    # Create formatters and add it to handlers
    c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)

    return logger