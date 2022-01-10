from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
from redbot.core.utils.common_filters import filter_invites, filter_various_mentions, escape_spoilers_and_mass_mentions
from discord_components import DiscordComponents, Button, ButtonStyle, Select, SelectOption
import asyncio
import datetime
import discord.utils 
import discord.ext
import discord
import os
import typing
from num2words import num2words

class Verification(commands.Cog):
    """Cog for approving members on public servers."""
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1312420691312, force_registration=True)
        self.config.register_guild(verifier_channel = None, cached_users = {}, invites = {})

    async def find_invite(self, member: discord.Member):
        async with self.config.guild(member.guild).invites() as invites_before_join:
            invites_after_join = await member.guild.invites()

            for invite in invites_before_join:
                for invite_after in invites_after_join:
                    if invite.code == invite_after.code:
                        if invite.uses < invite_after.uses:
                            invites_before_join = invites_after_join
                            return invite

        invites_before_join = invites_after_join
        return None

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id != 802882189602979881:
            return

        guild = member.guild

        verifier_channel_id = await self.config.guild(guild).verifier_channel()
        cached_users = await self.config.guild(guild).cached_users()

        if not verifier_channel_id:
            return

        channel = discord.utils.get(guild.channels, id = verifier_channel_id)
        
        avatar = member.avatar_url_as(static_format = "png")
        roles = member.roles[-1:0:-1]

        invite = await self.find_invite(member)

        if invite:
            invite_code = invite.code
            inviter = invite.inviter
        else:
            invite_code = inviter = None

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

        join_str = f"**{name}** joined the server for the {num2words(len(cached_users[member.id]) + 1, ordinal = True)} time!"

        if inviter:
            invite_str = f"{invite_code} (created by {inviter})"

        if roles:
            role_str = ", ".join([x.mention for x in roles])
        else:
            role_str = None

        e = discord.Embed(colour=member.colour)
        e.add_field(name = "Joined Discord on", value = created_on)
        e.add_field(name = "Joined this server on", value = joined_on)

        if join_str is not None:
            e.add_field(name = "Joined server with invite", value = invite_str)

        if role_str is not None:
            e.add_field(name = "Roles" if len(roles) > 1 else "Role", value = role_str, inline = False)

        e.set_footer(text = f"Member #{member_number} | User ID: {member.id}")
        e.set_author(name=f"{statusemoji} {name}", url = avatar)
        e.set_thumbnail(url = avatar)

        message = await channel.send(embed = e, components = [[Button(style = ButtonStyle.green, label = "Approve", custom_id = "approve", disabled = True),
                                                               Button(style = ButtonStyle.grey, emoji = self.bot.get_emoji(929343381409255454), custom_id = "sus", disabled = True),
                                                               Button(style = ButtonStyle.red, label = "Ban", custom_id = "ban", disabled = True),
                                                               Button(style = ButtonStyle.blue, emoji = "🔒", custom_id = "lock", disabled = False)]])

        cached_users[member.id].append(message.id)

    @commands.Cog.listener()
    async def on_button_click(self, interaction):
        buttons = interaction.message.components

        if interaction.custom_id == "approve":
            pass

        if interaction.custom_id == "sus":
            pass

        if interaction.custom_id == "ban":
            pass

        if interaction.custom_id == "lock":
            for action_bar in buttons:
                for button in action_bar:
                    if button.id == "lock":
                        button.emoji = "🔒" if str(button.emoji) == "🔓" else "🔓"
                    else:
                        button.disabled = not button.disabled
            await interaction.edit_origin(components = buttons)

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

