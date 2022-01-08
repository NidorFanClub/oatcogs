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

    @checks.mod_or_permissions(administrator=True)
    @commands.guild_only()
    @commands.command()
    async def button(self, ctx):
        async def callback(interaction):
            await interaction.send(content="Yay")

        e = discord.Embed(description = f"**moosey#9999 has joined the server.")
        e.add_field(name="Joined Discord on", value="June 15, 2016 11:32 AM\n(6 years ago)")
        e.add_field(name="Joined this server on", value="January 24, 2021 6:47 AM\n(a year ago)")
        e.set_footer(text="Member #1 | User ID: 192677766003556352")
        e.set_author(name="moosey#9999", url="https://cdn.discordapp.com/avatars/192677766003556352/1c1bbd93c523d443bd3acc4ad2e525a3.png?size=1024")
        e.set_thumbnail(url="https://cdn.discordapp.com/avatars/192677766003556352/1c1bbd93c523d443bd3acc4ad2e525a3.png?size=1024")

        await ctx.send(embed = e, components = [[self.bot.components_manager.add_callback(Button(style=ButtonStyle.green, label="Approve"), callback),
                                                 self.bot.components_manager.add_callback(Button(style=ButtonStyle.red, label="Banhammer"), callback)]])

