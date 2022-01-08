from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
from discord_components import (
    Button,
    ButtonStyle,
    Select,
    SelectOption,
    ComponentsBot,
    DiscordComponents
)
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

        await ctx.send(
            "Button callbacks!",
            components=[
                self.bot.components_manager.add_callback(
                    Button(style=ButtonStyle.blue, label="Click this"), callback
                ),
            ],
        )

    @checks.mod_or_permissions(administrator=True)
    @commands.guild_only()
    @commands.command()
    async def select(self, ctx):
        async def callback(interaction):
            await interaction.send(content="Yay")

        await ctx.send(
            "Select callbacks!",
            components=[
                self.bot.components_manager.add_callback(
                    Select(
                        options=[
                            SelectOption(label="a", value="a"),
                            SelectOption(label="b", value="b"),
                        ],
                    ),
                    callback,
                )
            ],
        )

