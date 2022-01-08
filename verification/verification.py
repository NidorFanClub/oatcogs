from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
from discord_components import DiscordComponents, Button, ButtonStyle, Select, SelectOption
import asyncio
import discord.utils 
import discord.ext
import discord
import os
import typing

class Verification(commands.Cog):
    """Cog for approving members on public servers."""
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1312420691312, force_registration=True)

    @bot.event
    async def on_button_click(interaction):
        await interaction.respond(content="Button Clicked")

    @checks.mod_or_permissions(administrator=True)
    @commands.guild_only()
    @commands.command()
    async def button(self, ctx):
        await ctx.send("i love my vegan friends. especially muradok", components = [[self.bot.components_manager.add_callback(Button(style = ButtonStyle.green, label = "Approve", custom_id = "approve")),
                                                                                    self.bot.components_manager.add_callback(Button(style = ButtonStyle.grey, emoji = bot.get_emoji(929343381409255454), custom_id = "sus"))
                                                                            self.bot.components_manager.add_callback(Button(style = ButtonStyle.red, label = "Ban", custom_id = "ban"))]])

