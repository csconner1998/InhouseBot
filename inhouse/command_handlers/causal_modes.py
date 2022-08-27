import discord
from inhouse.constants import *

class CasualModePicker(discord.ui.View):
    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.message.edit(content="You took too long! Disabled all the components.", view=self)

    @discord.ui.select(
        placeholder = "Choose on or more game type!",
        min_values = 1,
        max_values = 3,
        options = [
            discord.SelectOption(
                label="ARAM",
                # emoji=f"<:ARAM:{top_emoji_id}>"
                emoji=f"<:Top:{top_emoji_id}>"
            ),
            discord.SelectOption(
                label="TFT",
                #emoji=f"<:TFT:{mid_emoji_id}>"
                emoji=f"<:jungle:{jg_emoji_id}>"
            ),
            discord.SelectOption(
                label="Normals",
                #emoji=f"<:POGGIES~1:{jg_emoji_id}"
                emoji=f"<:Mid:{mid_emoji_id}>"
            )
        ]
    )
    async def select_callback(self, select, interaction):
        await interaction.response.send_message(f"You picked {select.values}")