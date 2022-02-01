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

    @checks.mod()
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

    @checks.mod()
    @commands.guild_only()
    @commands.command()
    async def get_channel_activity(self, ctx):
        """
        Return a text file (csv) of channels sorted by their messages/activity
        """
        # there's definitely a more pythonic way to do all this...
        async with ctx.channel.typing():
            output = "channel_name,messages\n"
            channels = {}
            for channel in ctx.guild.text_channels:
                counter = 0
                try:
                    async for message in channel.history(limit=None):
                        counter += 1
                except discord.Forbidden:
                    pass
                else:
                    channels[f"{channel.id} ({channel.name})"] = counter


            sorted_channels = dict(sorted(channels.items(), key=lambda item: item[1], reverse=True))
            for channel, message_count in sorted_channels.items():
                output += f"{channel},{message_count}\n"

            await ctx.send(file=text_to_file(output))
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
