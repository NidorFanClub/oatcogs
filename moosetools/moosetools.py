from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
from redbot.core.utils.chat_formatting import text_to_file
import asyncio
import discord.utils 
import discord.ext
import discord
import os
import typing

class MooseTools(commands.Cog):
    """various commands that don't deserve their own cog."""

    def __init__(self):
        self.config = Config.get_conf(self, identifier=13121311231233, force_registration=True)

    @checks.mod_or_permissions(administrator=True)
    @commands.guild_only()
    @commands.command()
    async def get_member_ids(self, ctx):
        """
        Returns all member IDs in the server as a text file
        """
        user_id_list = ""

        for user in ctx.guild.members:
            user_id_list += str(user.id) + "\n"

        await ctx.send(file = text_to_file(user_id_list))
        await ctx.tick()

    @commands.command()
    @commands.guild_only()
    async def avatar(self, ctx, member: discord.Member):
        """
        Returns a member's avatar url.
        """
        if not member:
            member = ctx.author

        if member.is_avatar_animated():
            avatar_url = member.avatar_url_as(format = "gif")
        if not member.is_avatar_animated():
            avatar_url = member.avatar_url_as(static_format = "png")

        await ctx.send(f"{avatar_url}")
