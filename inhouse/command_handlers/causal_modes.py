import discord
import inhouse.constants
from inhouse.command_handlers.queue import Queue

class CasualModePicker(discord.ui.View):
    def __init__(self, *items, timeout = 180, ctx: discord.ApplicationContext):
        super().__init__(*items, timeout=timeout)
        self.ctx = ctx

    @discord.ui.button(label="Casual Inhouse", style=discord.ButtonStyle.primary, emoji="⚔️")
    async def casual_inhouse_callback(self, button, interaction):
        await self.disable_buttons(interaction)
        print("Chose Casual Inhouses")
        if inhouse.constants.casual_queue != None:
            await inhouse.constants.casual_queue.queue_message.reply("Queue is already open! React to the above message")
            return
        inhouse.constants.casual_queue = Queue(ctx=self.ctx)
        await inhouse.constants.casual_queue.create_queue_message(inhouse.constants.server_roles.casual_inhouse)
        
    # @discord.ui.button(label="Normal Game", style=discord.ButtonStyle.primary, emoji="♻️")
    # async def normal_game_callback(self, button, interaction):
    #     await self.disable_buttons(interaction)
    #     print("Chose Norms")

    # @discord.ui.button(label="ARAM", style=discord.ButtonStyle.primary, emoji="♻️")
    # async def aram_callback(self, button, interaction):
    #     await self.disable_buttons(interaction)
    #     print("Chose ARAM")

    # @discord.ui.button(label="FLEX", style=discord.ButtonStyle.primary, emoji="♻️")
    # async def flex_callback(self, button, interaction):
    #     await self.disable_buttons(interaction)
    #     print("Chose Flex")

    async def disable_buttons(self, interaction):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)  