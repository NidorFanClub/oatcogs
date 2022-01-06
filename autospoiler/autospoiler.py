from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
from datetime import datetime, timedelta
import asyncio
import discord.utils 
import discord.ext
import discord
import os
import re
import typing

class Autospoiler(commands.Cog):
    """Autospoil certain words!"""
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=4128309349, force_registration=True)
        self.config.register_guild(filtered_words = [])

    @commands.group(autohelp=True)
    @commands.guild_only()
    @checks.mod_or_permissions(manage_messages=True)
    async def autospoil(self, ctx: commands.Context):
        f"Settings for autospoiling."

    @autospoil.command(name = "add", aliases = ['insert'])
    async def autospoil_add(self, ctx:commands.Context, *args):
        if not args:
            return await ctx.send("Please provide a word or a list of words separated by a space.")

        words_added = 0

        async with self.config.guild(ctx.guild).filtered_words() as filtered_words:
            for word in args:
                if word.lower() not in filtered_words:
                    filtered_words.append(word.lower())
                    words_added += 1

        await ctx.send(f"Added {words_added} new word(s) to the list of filtered words!")

    @autospoil.command(name = "remove", aliases = ['delete'])
    async def autospoil_remove(self, ctx:commands.Context, *args):
        if not args:
            return await ctx.send("Please provide a word or a list of words separated by a space.")

        words_removed = 0

        async with self.config.guild(ctx.guild).filtered_words() as filtered_words:
            for word in args:
                if word.lower() in filtered_words:
                    filtered_words.remove(word.lower())
                    words_removed += 1

        await ctx.send(f"Removed {words_removed} word(s) from the list of filtered words!")

    @autospoil.command(name = "clear")
    async def autospoil_clear(self, ctx:commands.Context):
        words_removed = 0

        async with self.config.guild(ctx.guild).filtered_words() as filtered_words:
            words_removed = len(filtered_words)
            for word in filtered_words:
                filtered_words.clear()

        await ctx.send(f"Removed {words_removed} word(s) from the list of filtered words!")

    @autospoil.command(name = "list", aliases = ['output', 'print', 'words'])
    async def autospoil_list(self, ctx:commands.Context):
        e = discord.Embed(title="", colour=ctx.author.color)
        e.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)

        word_list = ""

        async with self.config.guild(ctx.guild).filtered_words() as filtered_words:
            for word in filtered_words:
                word_list += word + "\n"

        if not word_list:
            word_list = "Empty"

        e.add_field(name="Filtered Words", value=word_list)

        e.timestamp = datetime.utcnow()
        await ctx.send(embed=e)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None:
            return

        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return

        valid_user = isinstance(message.author, discord.Member) and not message.author.bot
        if not valid_user:
            return

        if await self.bot.is_automod_immune(message):
            return

        new_message = message.content

        message_needs_spoiling = False

        async with self.config.guild(message.guild).filtered_words() as filtered_words:
            for word in filtered_words:
                if word.lower() in new_message.lower():
                    new_message.replace("|", "")
                    new_message = "||" + new_message + "||"
                    message_needs_spoiling = True
                    break

        if message_needs_spoiling:
            try:
                await message.delete()
            except discord.HTTPException:
                pass
            e = discord.Embed(title="", description = f"{new_message}", colour=message.author.color)
            e.set_author(name=message.author, icon_url=message.author.avatar_url)
            e.timestamp = message.created_at

            if message.reference:
                original_message = await message.channel.fetch_message(id=message.reference.message_id)
                await original_message.reply(embed=e, mention_author=False)
            else:
                await message.channel.send(embed=e)

    @commands.Cog.listener()
    async def on_message_edit(self, _prior, message):
        await self.on_message(message)
