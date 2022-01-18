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
    """various commands that don't deserve their own cog."""
    def __init__(self):
        self.config = Config.get_conf(self, identifier=13121311231233, force_registration=True)

    @checks.mod_or_permissions(administrator=True)
    @commands.guild_only()
    @commands.command()
    async def member_ids(self, ctx):
        """
        Returns all member IDs in the server as a formatted list of
        """
        with open("member_ids.txt", "w") as file:
            for user in ctx.guild.members:
                file.write(str(user.id) + "\n")

        with open("member_ids.txt", "rb") as file:
            await ctx.send(file=discord.File(file, "member_ids.txt"))
            await ctx.tick()

    @commands.command()
    @commands.guild_only()
    async def avatar(self, ctx, member: discord.Member):
        """
        Returns a member's avatar.
        """
        if not member:
            member = ctx.author

        if member.is_avatar_animated():
            avatar = member.avatar_url_as(format="gif")
        if not member.is_avatar_animated():
            avatar = member.avatar_url_as(static_format="png")

        await ctx.send(f"{avatar}")

