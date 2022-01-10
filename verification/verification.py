from redbot.core import Config, checks, commands, modlog
from redbot.core.utils.common_filters import filter_invites, filter_various_mentions, escape_spoilers_and_mass_mentions
from discord_components import DiscordComponents, Button, ButtonStyle, Select, SelectOption
import asyncio
from datetime import datetime, timezone, timedelta
import discord.utils 
import discord.ext
import discord
import os
import typing
from num2words import num2words
from collections import defaultdict

class Verification(commands.Cog):
    """Cog for approving members on public servers."""
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1312420691312, force_registration=True)
        self.config.register_guild(verifier_channel = None, cached_users = {}, cached_invites = {}, approved_roles = [], sus_roles = [], removed_roles = [])

    async def get_user(self, message: discord.Message):
        async with self.config.guild(message.guild).cached_users() as cached_users:
            for user_id, cached_messages in cached_users.items():
                for cached_message_id in cached_messages:
                    if cached_message_id == message.id:
                        user = discord.utils.get(message.guild.members, id = int(user_id))
                        return user
        return None

    async def update_invites(self, guild: discord.Guild):
        async with self.config.guild(guild).cached_invites() as cached_invites:
            for invite in await guild.invites():
                if invite.id not in cached_invites:
                    cached_invites[invite.id] = invite.uses

    async def find_invite(self, guild: discord.Guild):
        invites_after_join = await guild.invites()
        invites_before_join = await self.config.guild(guild).cached_invites()

        for invite_after in invites_after_join:
            for invite_before_id in invites_before_join:
                if invite_before_id == invite_after.code:
                    if invites_before_join[invite_before_id] < invite_after.uses:
                        return invite_before_id
        return None

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self.update_invites(member.guild)

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

        invite_id = await self.find_invite(guild)

        if invite_id:
            invite = discord.utils.get(await guild.invites(), id = invite_id)
        else:
            invite = None

        await self.update_invites(guild)

        if joined_at := member.joined_at:
            joined_at = joined_at.replace(tzinfo=timezone.utc)

        user_created = int(member.created_at.replace(tzinfo=timezone.utc).timestamp())

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

        async with self.config.guild(guild).cached_users() as cached_users:
            if str(member.id) not in cached_users:
                cached_users[str(member.id)] = []

            join_str = f"**{name}** joined the server for the {num2words(len(cached_users[str(member.id)]) + 1, ordinal = True)} time!"

        if invite:
            invite_str = f"<{invite.url}> ({invite.inviter})"
        else:
            invite_str = None

        if roles:
            role_str = ", ".join([x.mention for x in roles])
        else:
            role_str = None

        e = discord.Embed(description = join_str, colour=member.colour)
        e.add_field(name = "Joined Discord on", value = created_on)
        e.add_field(name = "Joined server on", value = joined_on)

        if invite_str is not None:
            e.add_field(name = "Joined with invite", value = invite_str)

        if role_str is not None:
            e.add_field(name = "Roles" if len(roles) > 1 else "Role", value = role_str, inline = False)

        e.set_footer(text = f"Member #{member_number} | User ID: {member.id}")
        e.set_author(name=f"{statusemoji} {name}", url = avatar)
        e.set_thumbnail(url = avatar)

        message = await channel.send(embed = e, components = [[Button(style = ButtonStyle.green, label = "Approve", custom_id = "approve", disabled = True),
                                                               Button(style = ButtonStyle.grey, emoji = self.bot.get_emoji(929343381409255454), custom_id = "sus", disabled = True),
                                                               Button(style = ButtonStyle.red, label = "Ban", custom_id = "ban", disabled = True),
                                                               Button(style = ButtonStyle.blue, emoji = "🔒", custom_id = "lock", disabled = False)]])

        async with self.config.guild(guild).cached_users() as cached_users:
            cached_users[str(member.id)].append(int(message.id))

    async def add_roles(self, role_list, member: discord.Member):
        for role_id in role_list:
            role = discord.utils.get(member.guild.roles, id = int(role_id))
            try:
                await member.add_roles(role)
            except:
                pass

    async def remove_roles(self, role_list, member: discord.Member):
        for role_id in role_list:
            role = discord.utils.get(member.guild.roles, id = int(role_id))
            try:
                await member.remove_roles(role)
            except:
                pass

    @commands.Cog.listener()
    async def on_button_click(self, interaction):
        buttons = interaction.message.components

        member = await self.get_user(interaction.message)

        if not member:
            return

        if not interaction.user.top_role > member.top_role and not await self.bot.is_owner(interaction.user):
            return

        if interaction.custom_id == "approve":
            await self.add_roles(member, await self.config.guild(member.guild).approved_roles())
            await self.remove_roles(member, await self.config.guild(member.guild).removed_roles())
            await interaction.edit_origin(components = [[Button(style = ButtonStyle.green, label = f"Approved by {interaction.user.name}", custom_id = "approve", disabled = True)]])

        if interaction.custom_id == "sus":
            await self.add_roles(member, await self.config.guild(member.guild).sus_roles())
            await self.remove_roles(member, await self.config.guild(member.guild).removed_roles())
            await interaction.edit_origin(components = [[Button(style = ButtonStyle.green, label = f"Approved by {interaction.user.name}", custom_id = "approve", disabled = True)]])

        if interaction.custom_id == "ban":
            try:
                await member.ban(reason="troll in verification")
            except discord.NotFound:
                pass
            await modlog.create_case(self.bot, member.guild, datetime.now(tz = timezone.utc), "ban", member, interaction.user, reason = "troll in verification", until = None, channel = None)
            await interaction.edit_origin(components = [[Button(style = ButtonStyle.red, label = f"Banned by {interaction.user.name}", custom_id = "ban", disabled = True)]])

        if interaction.custom_id == "lock":
            for action_bar in buttons:
                for button in action_bar:
                    if button.id == "lock":
                        button.emoji = "🔒" if str(button.emoji) == "🔓" else "🔓"
                    else:
                        button.disabled = not button.disabled
            await interaction.edit_origin(components = buttons)

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

    @verification.group(name = "add")
    @checks.mod_or_permissions(manage_messages=True)
    async def verification_add(self, ctx: commands.Context) -> None:
        f"Add roles to the verification settings."
        pass

    @verification_add.command(name = "approved_roles", require_var_positional=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def verification_add_approved_roles(self, ctx, roles: commands.Greedy[discord.Role]):
        async with self.config.guild(ctx.guild).approved_roles() as approved_roles:
            roles_added = 0
            for approved_role in roles:
                try:
                    roles_added += 1
                    approve_roles.append(approved_role.id)
                except:
                    pass
            await ctx.send(f"Added {roles_added} role(s) to the list of approved roles!")
        await ctx.tick()

    @verification_add.command(name = "sus_roles", require_var_positional=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def verification_add_sus_roles(self, ctx, roles: commands.Greedy[discord.Role]):
        async with self.config.guild(ctx.guild).sus_roles() as sus_roles:
            roles_added = 0
            for sus_role in roles:
                try:
                    roles_added += 1
                    sus_roles.append(sus_role.id)
                except:
                    pass
            await ctx.send(f"Added {roles_added} role(s) to the list of sus roles!")
        await ctx.tick()

    @verification_add.command(name = "removed_roles", require_var_positional=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def verification_add_removed_roles(self, ctx, roles: commands.Greedy[discord.Role]):
        async with self.config.guild(ctx.guild).removed_roles() as removed_roles:
            roles_added = 0
            for removed_role in roles:
                try:
                    roles_added += 1
                    removed_roles.append(removed_role.id)
                except:
                    pass
            await ctx.send(f"Added {roles_added} role(s) to the list of removed roles!")
        await ctx.tick()

    @verification.command(name = "clear")
    @checks.mod_or_permissions(manage_messages=True)
    async def verification_clear(self, ctx: commands.Context):
        f"Clear roles from the verification settings."
        await self.config.guild(ctx.guild).approved_roles().clear()
        await self.config.guild(ctx.guild).removed_roles().clear()
        await self.config.guild(ctx.guild).banned_roles().clear()
        await self.config.guild(ctx.guild).verifier_channel.set(None)

    @verification_set.command(name = "verifier_channel")
    @checks.mod_or_permissions(manage_messages=True)
    async def verification_set_verifier_channel(self, ctx, channel: discord.TextChannel):
        await self.config.guild(ctx.guild).verifier_channel.set(channel.id)
        await ctx.tick()

