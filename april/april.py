import discord
import discord.utils
import discord.ext
import re
import emoji

from redbot.core import commands, Config, bank, checks


class April(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None:
            return
        valid = True
        valid2 = True
        msg = message
        author = message.author
        valid_user = isinstance(author, discord.Member) and not author.bot
        if not valid_user:
            return
        channels = [926112975813750796, 927783621794877460, 926113551968526376, 926113675419471972,
                    927518938919735326, 927518938919735326, 927539973459169302, 928689945080627201, 930531314363424808]
        if message.channel.id in channels:

            if len(message.attachments) == 0:
                x = re.search(r'^<a.*:|<:.*>$', msg.content)
                if not x:
                    valid = False
                else:
                    valid = True
                x = re.search(r'>*\s[^\s]*\s<', msg.content)
                if x:
                    valid = False

                if valid == False:
                    for symbol in msg.content:
                        if symbol not in emoji.UNICODE_EMOJI['en']:

                            valid2 = False
                        else:
                            i = msg.content.replace(symbol, '')
                            x = re.search(r'^\s*<:.*>\s*$', str(i))
                            if x:
                                valid = True
                                valid2 = True

            if valid == False and valid2 == False:
                try:
                    await message.delete()
                except discord.HTTPException:
                    pass

    @commands.Cog.listener()
    async def on_message_edit(self, _prior, message):
        await self.on_message(message)
