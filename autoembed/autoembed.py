from redbot.core import commands, Config, checks
from redbot.core.utils.chat_formatting import humanize_list
import asyncio
import discord.utils
import discord.ext
import discord

class Autoembed(commands.Cog):
    """Autoembed in channels!"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=783458793432, force_registration=True)
        self.config.register_guild(enabled=False, whitelist=[], blacklist=[], all_channels=False)

    @commands.group(autohelp=True)
    @commands.guild_only()
    @checks.admin()
    async def autoembed(self, ctx: commands.Context):
        """Settings for autoembedding."""

    @autoembed.command(name="enable")
    async def autoembed_enable(self, ctx: commands.Context, toggle: bool):
        """Toggle autoembedding in this guild.

        This is disabled by default."""
        await self.config.guild(ctx.guild).enabled.set(toggle)
        await ctx.send(f"Autoembed has been turned {'on' if toggle else 'off'}.")

    @autoembed.command(name="all")
    async def autoembed_all(self, ctx: commands.Context, toggle: bool):
        """Toggle autoembedding in all channels. **Use with caution.**

        This is disabled by default. This can easily reach ratelimits on large servers."""
        await self.config.guild(ctx.guild).all_channels.set(toggle)
        await ctx.send(f"Autoembed has been turned {'on' if toggle else 'off'} in all channels.")

    @autoembed.group(name="whitelist", autohelp=True)
    @commands.guild_only()
    async def autoembed_whitelist(self, ctx: commands.Context):
        """The list of channels where autoembedding is on."""

    @autoembed_whitelist.command(name="add", require_var_positional=True)
    async def autoembed_whitelist_add(self, ctx, *channels: discord.TextChannel):
        """Add channels to the whitelist"""
        async with self.config.guild(ctx.guild).whitelist() as whitelist:
            channels_added = [channel.id for channel in channels if channel.id not in whitelist]
            whitelist.extend(channels_added)

            if not channels_added:
                await ctx.send("Channels(s) already in whitelist")
                return

            await ctx.send(f"Added {humanize_list([ctx.guild.get_channel(channel_id).mention for channel_id in channels_added])} to whitelist")

    @autoembed_whitelist.command(name="remove", require_var_positional=True)
    async def autoembed_whitelist_remove(self, ctx, *channels: discord.TextChannel):
        """Remove channels from the whitelist"""
        async with self.config.guild(ctx.guild).whitelist() as whitelist:
            channels_removed = [channel.id for channel in channels if channel.id in whitelist]

            if not channels_removed:
                await ctx.send("Channels(s) not in whitelist")
                return

            for channel in channels_removed:
                whitelist.remove(channel)

            await ctx.send(f"Removed {humanize_list([ctx.guild.get_channel(channel_id).mention for channel_id in channels_removed])} from whitelist")

    @autoembed.group(name="blacklist", autohelp=True)
    @commands.guild_only()
    async def autoembed_blacklist(self, ctx: commands.Context):
        """The list of channels where autoembedding is off.

        Generally unncessary unless autoembedding in all channels is enabled (but why would you do that?)"""

    @autoembed_blacklist.command(name="add", require_var_positional=True)
    async def autoembed_blacklist_add(self, ctx, *channels: discord.TextChannel):
        """Add channels to the blacklist"""
        async with self.config.guild(ctx.guild).blacklist() as blacklist:
            channels_added = [channel.id for channel in channels if channel.id not in blacklist]
            blacklist.extend(channels_added)

            if not channels_added:
                await ctx.send("Channels(s) already in blacklist")
                return

            await ctx.send(f"Added {humanize_list([ctx.guild.get_channel(channel_id).mention for channel_id in channels_added])} to blacklist")

    @autoembed_blacklist.command(name="remove", require_var_positional=True)
    async def autoembed_blacklist_remove(self, ctx, *channels: discord.TextChannel):
        """Remove channels from the blacklist"""
        async with self.config.guild(ctx.guild).blacklist() as blacklist:
            channels_removed = [channel.id for channel in channels if channel.id in blacklist]

            if not channels_removed:
                await ctx.send("Channels(s) not in blacklist")
                return

            for channel in channels_removed:
                blacklist.remove(channel)

            await ctx.send(f"Removed {humanize_list([ctx.guild.get_channel(channel_id).mention for channel_id in channels_removed])} from blacklist")

    @autoembed.command(name="reset", aliases=["clear"])
    async def autospoiler_reset(self, ctx: commands.Context):
        """Reset channel settings to default."""
        async with self.config.guild(ctx.guild).whitelist() as whitelist:
            whitelist.clear()
        async with self.config.guild(ctx.guild).blacklist() as blacklist:
            blacklist.clear()
        await self.config.guild(ctx.guild).enabled.set(False)
        await self.config.guild(ctx.guild).all_channels.set(False)
        await ctx.tick()

    @autoembed.command(name="list")
    async def autoembed_list(self, ctx):
        """List current guild settings for autoembedding"""
        e = discord.Embed(title="", colour=ctx.author.color)
        e.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)

        async with self.config.guild(ctx.guild).whitelist() as whitelist:
            if not whitelist:
                whitelisted_channels = "Empty"
            else:
                channels = [ctx.guild.get_channel(channel_id).mention for channel_id in whitelist]
                whitelisted_channels = "\n".join(channels)

        async with self.config.guild(ctx.guild).blacklist() as blacklist:
            if not blacklist:
                blacklisted_channels = "Empty"
            else:
                channels = [ctx.guild.get_channel(channel_id).mention for channel_id in blacklist]
                blacklisted_channels = "\n".join(channels)

        e.add_field(name="Enabled", value=str(await self.config.guild(ctx.guild).enabled()), inline=False)
        e.add_field(name="All Channels", value=str(await self.config.guild(ctx.guild).all_channels()), inline=False)
        e.add_field(name="Whitelist", value=whitelisted_channels, inline=False)
        e.add_field(name="Blacklist", value=blacklisted_channels, inline=False)

        await ctx.send(embed=e)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None:
            return

        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return

        if message.author.bot:
            return

        if not await self.bot.ignored_channel_or_guild(message):
            return

        if not await self.config.guild(message.guild).enabled():
            return

        async with self.config.guild(message.guild).blacklist() as blacklist:
            if message.channel in [message.guild.get_channel(channel_id) for channel_id in blacklist]:
                return

        async with self.config.guild(message.guild).whitelist() as whitelist:
            if message.channel not in [message.guild.get_channel(channel_id) for channel_id in whitelist]:
                if not await self.config.guild(message.guild).all_channels():
                    return

        try:
            await message.delete()
        except Exception:
            pass

        e = discord.Embed(description=message.content, colour=message.author.color)
        e.set_author(name=message.author, icon_url=message.author.avatar_url)
        e.timestamp = message.created_at

        if message.reference:
            replied_to = await message.channel.fetch_message(id=message.reference.message_id)
            await replied_to.reply(embed=e, mention_author=False)
        else:
            await message.channel.send(embed=e)
