from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
from redbot.core.utils.chat_formatting import text_to_file
from datetime import datetime, timedelta
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
            output = "channel_name,category,messages,unique_members,days_since_created,messages_per_day,messages_this_week,messages_this_month\n"
            channels = []
            now = datetime.today()
            for channel in ctx.guild.text_channels:
                counter = 0
                week_counter = 0
                month_counter = 0
                unique_members = []
                try:
                    async for message in channel.history(limit=31500):
                        counter += 1
                        message_delta = now - message.created_at
                        if message_delta.days <= 7:
                            week_counter += 1
                        if message_delta.days <= 30:
                            month_counter += 1
                        if message.author.id not in unique_members:
                            unique_members.append(message.author.id)
                except discord.Forbidden:
                    pass
                else:
                    channel_dict = {}
                    channel_delta = now - channel.created_at
                    channel_dict["name"] = channel.name
                    channel_dict["category"] = channel.category.name
                    channel_dict["id"] = channel.id
                    channel_dict["messages"] = counter
                    channel_dict["unique_members"] = len(unique_members)
                    channel_dict["days_since_created"] = channel_delta.days
                    channel_dict["messages_per_day"] = (counter / int(channel_delta.days)) if int(channel_delta.days) else 0
                    channel_dict["messages_this_week"] = week_counter
                    channel_dict["messages_this_month"] = week_counter
                    channels.append(channel_dict)

            for channel in channels:
                output += f"{channel['name']},{channel['category']},{channel['messages']},{channel['unique_members']},{channel['days_since_created']},{channel['messages_per_day'],{channel['messages_this_week']},{channel['messages_this_month']:.2f}\n"

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
