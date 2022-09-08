import discord
import inhouse.constants
from inhouse.command_handlers.queue import Queue, AramQueue

class CasualModePicker(discord.ui.View):
    def __init__(self, *items, timeout = 180, ctx: discord.ApplicationContext):
        super().__init__(*items, timeout=timeout)
        self.ctx = ctx

    @discord.ui.button(label="Casual Inhouse - SR", style=discord.ButtonStyle.primary, emoji="⚔️")
    async def casual_inhouse_callback(self, button, interaction):
        await self.disable_buttons(interaction)
        print("Chose Casual Inhouses SR")
        if inhouse.global_objects.casual_queue != None:
            await inhouse.global_objects.casual_queue.queue_message.reply("Queue is already open! React to the above message")
            return
        inhouse.global_objects.casual_queue = Queue(ctx=self.ctx)
        await inhouse.global_objects.casual_queue.create_queue_message(inhouse.constants.server_roles.casual_inhouse)
        
    @discord.ui.button(label="Casual Inhouse - ARAM", style=discord.ButtonStyle.primary, emoji=f"<:ARAM:{inhouse.constants.aram_emoji_id}>")
    async def normal_game_callback(self, button, interaction):
        await self.disable_buttons(interaction)
        print("Chose Casual Inhouses ARAM")
        if inhouse.global_objects.casual_queue_aram != None:
            await inhouse.global_objects.casual_queue_aram.queue_message.reply("Queue is already open! React to the above message")
            return
        inhouse.global_objects.casual_queue_aram = AramQueue(ctx=self.ctx)
        await inhouse.global_objects.casual_queue_aram.create_queue_message(inhouse.constants.server_roles.casual_inhouse)

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