from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
import asyncio
import discord.utils 
import discord.ext
import discord
import os
import typing

class moosetools(commands.Cog):
    """various tools that don't deserve their own cog."""
    def __init__(self):
        self.config = Config.get_conf(self, identifier=13121311231233, force_registration=True)

    @checks.mod_or_permissions(administrator=True)
    @commands.guild_only()
    @commands.command()
    async def member_ids(self, ctx):
        with open("member_ids.txt", "w") as file:
            for user in ctx.guild.members:
                file.write(str(user.id) + "\n")

        with open("member_ids.txt", "rb") as file:
            await ctx.send(file=discord.File(file, "member_ids.txt"))
            await ctx.tick()
