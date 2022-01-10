from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
from redbot.core.utils.common_filters import filter_invites, filter_various_mentions, escape_spoilers_and_mass_mentions
from discord_components import DiscordComponents, Button, ButtonStyle, Select, SelectOption
from datetime import datetime, timedelta
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
        self.config.register_guild(verifier_channel = None, cached_users = {}, invites = {})

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id != 802882189602979881:
            return

        guild = member.guild

        verifier_channel_id = await self.config.guild(guild).verifier_channel()

        if not verifier_channel_id:
            return

        channel = discord.utils.get(guild.channels, id = verifier_channel_id)
        
        avatar = member.avatar_url_as(static_format = "png")
        roles = member.roles[-1:0:-1]

        await channel.send(f"{channel.id}, {member.guild.id}")

        cached_users = await self.config.guild(guild).cached_users()

        invite_code = "Unknown"
        inviter = "unknown"

        async with self.config.guild(guild).invites() as invites_before_join:
            invites_after_join = await member.guild.invites()

            for invite in invites_before_join:
                for invite_after in invites_after_join:
                    if invite.code == invite_after.code:
                        if invite.uses < invite_after.uses:
                            invite_code = invite.code
                            inviter = invite.inviter

            invites_before_join = invites_after_join

        if joined_at := member.joined_at:
            joined_at = joined_at.replace(tzinfo=datetime.timezone.utc)

        user_created = int(member.created_at.replace(tzinfo=datetime.timezone.utc).timestamp())

        member_number = (sorted(guild.members, key=lambda m: m.joined_at or ctx.message.created_at).index(member) + 1)

        created_on = "<t:{0}>\n(<t:{0}:R>)".format(user_created)

        if joined_at is not None:
            joined_on = "<t:{0}>\n(<t:{0}:R>)".format(int(joined_at.timestamp()))
        else:
            joined_on = "Unknown"

        if any(a.type is discord.ActivityType.streaming for a in member.activities):
            statusemoji = "\N{LARGE PURPLE CIRCLE}"
        elif member.status.name == "online":
            statusemoji = "\N{LARGE GREEN CIRCLE}"
        elif member.status.name == "offline":
            statusemoji = "\N{MEDIUM WHITE CIRCLE}\N{VARIATION SELECTOR-16}"
        elif member.status.name == "dnd":
            statusemoji = "\N{LARGE RED CIRCLE}"
        elif member.status.name == "idle":
            statusemoji = "\N{LARGE ORANGE CIRCLE}"

        name = str(member)
        name = " ~ ".join((name, member.nick)) if member.nick else name
        name = filter_invites(name)

        if member.id not in cached_users:
            cached_users[member.id] = []

        ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])

        join_str = f"**{name}** joined the server for the {ordinal(cached_users[member.id].count() + 1)} time!"
        invite_str = f"{invite_code} (created by {inviter.name})"

        if roles:
            role_str = ", ".join([x.mention for x in roles])

        e = discord.Embed(colour=member.colour)
        e.add_field(name = "Joined Discord on", value = created_on)
        e.add_field(name = "Joined this server on", value = joined_on)
        e.add_field(name = "Joined server with invite", value = invite_str)
        e.set_footer(text = f"Member #{member_number} | User ID: {member.id}")

        if role_str is not None:
            e.add_field(name = "Roles" if len(roles) > 1 else "Role", value = role_str, inline = False)

        e.set_author(name=f"{statusemoji} {name}", url = avatar)
        e.set_thumbnail(url = avatar)

        message = await channel.send(embed = e, components = [[Button(style = ButtonStyle.green, label = "Approve", custom_id = "approve", disabled = True),
                                                               Button(style = ButtonStyle.grey, emoji = self.bot.get_emoji(929343381409255454), custom_id = "sus", disabled = True),
                                                               Button(style = ButtonStyle.red, label = "Ban", custom_id = "ban", disabled = True),
                                                               Button(style = ButtonStyle.blue, emoji = "🔓", custom_id = "lock", disabled = False)]])

        cached_users[member.id].append(message.id)

    @commands.Cog.listener()
    async def on_button_click(self, interaction):
        buttons = interaction.message.components

        if interaction.custom_id == "lock":
            for action_bar in buttons:
                for button in action_bar:
                    if button.id == "lock":
                        button.emoji = "🔓" if str(button.emoji) == "🔒" else "🔒"
                    else:
                        button.disabled = not button.disabled
            await interaction.edit_origin(components = buttons)

        if interaction.custom_id == "approve":
            pass

        if interaction.custom_id == "sus":
            pass

        if interaction.custom_id == "ban":
            pass

        #await interaction.respond(type = 6)

    @commands.group(name = "verification")
    @checks.mod_or_permissions(manage_messages=True)
    async def verification(self, ctx: commands.Context) -> None:
        f"Adjust or debug verification settings."
        pass

    @verification.group(name = "set")
    @checks.mod_or_permissions(manage_messages=True)
    async def verification_set(self, ctx: commands.Context) -> None:
        f"Adjust or debug verification settings."
        pass

    @verification_set.command(name = "verifier_channel")
    @checks.mod_or_permissions(manage_messages=True)
    async def verification_set_verifier_channel(self, ctx, channel: discord.TextChannel):
        await self.config.guild(ctx.guild).verifier_channel.set(channel.id)
        await ctx.tick()

