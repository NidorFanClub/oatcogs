from redbot.core import Config, checks, commands, modlog
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
        self.config.register_guild(verifier_channel = None, approval_channel = None, approval_message = "", cached_users = {}, cached_invites = {}, approved_roles = [], sus_roles = [], removed_roles = [], verifier_roles = [])

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
                cached_invites.update({invite.id: invite.uses})


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
    async def on_invite_create(self, invite: discord.Invite):
        await self.update_invites(invite.guild)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self.update_invites(member.guild)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild

        verifier_channel_id = await self.config.guild(guild).verifier_channel()

        channel = discord.utils.get(guild.channels, id = verifier_channel_id)

        if not channel:
            return
        
        avatar = member.avatar_url_as(static_format = "png")
        roles = member.roles[-1:0:-1]

        invite_id = await self.find_invite(guild)

        if invite_id:
            invite = discord.utils.get(await guild.invites(), id = invite_id)
        elif guild.vanity_invite():
            invite = await guild.vanity_invite()
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

        async with self.config.guild(guild).cached_users() as cached_users:
            if str(member.id) not in cached_users:
                cached_users[str(member.id)] = []

            join_str = f"**{member.mention}** joined the server for the {num2words(len(cached_users[str(member.id)]) + 1, ordinal = True)} time!"

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
        e.set_author(name=f"{statusemoji} {member.name}", url = avatar)
        e.set_thumbnail(url = avatar)

        message = await channel.send(embed = e, components = [[Button(style = ButtonStyle.green, label = "Approve", custom_id = "approve", disabled = True),
                                                               Button(style = ButtonStyle.grey, emoji = self.bot.get_emoji(929343381409255454), custom_id = "sus", disabled = True),
                                                               Button(style = ButtonStyle.red, label = "Ban", custom_id = "ban", disabled = True),
                                                               Button(style = ButtonStyle.blue, emoji = "🔒", custom_id = "lock", disabled = False)]])

        async with self.config.guild(guild).cached_users() as cached_users:
            cached_users[str(member.id)].append(int(message.id))

    async def add_roles(self, member: discord.Member, role_list):
        for role_id in role_list:
            role = discord.utils.get(member.guild.roles, id = int(role_id))
            try:
                await member.add_roles(role)
            except:
                pass

    async def remove_roles(self, member: discord.Member, role_list):
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

        verifier = False
        verifier_roles = await self.config.guild(member.guild).verifier_roles()
        approved_roles = await self.config.guild(member.guild).approved_roles()
        approval_channel = await self.config.guild(member.guild).approval_channel()
        approval_message = await self.config.guild(member.guild).approval_message()

        for verifier_role_id in verifier_roles:
            role = discord.utils.get(member.guild.roles, id = int(verifier_role_id))
            if role in interaction.user.roles:
                verifier = True

        for approved_role_id in approved_roles:
            role = discord.utils.get(member.guild.roles, id = int(approved_role_id))
            if role in member.roles:
                return

        if not await self.bot.is_owner(interaction.user) and not verifier:
            return

        cached_users = await self.config.guild(member.guild).cached_users()

        if interaction.custom_id == "approve":
            await self.remove_roles(member, await self.config.guild(member.guild).removed_roles())
            await self.add_roles(member, await self.config.guild(member.guild).approved_roles())
            new_buttons = [[Button(style = ButtonStyle.green, label = f"Approved by {interaction.user.name}", custom_id = "approve", disabled = True)]]

            if approval_channel is not None and approval_message is not None:
                channel = discord.utils.get(member.guild.channels, id = int(approval_channel))
                msg = f"Welcome, {member.mention}! " + approval_message
                await channel.send(msg)

        elif interaction.custom_id == "sus":
            await self.remove_roles(member, await self.config.guild(member.guild).removed_roles())
            await self.add_roles(member, await self.config.guild(member.guild).sus_roles())
            new_buttons = [[Button(style = ButtonStyle.green, label = "Approve", custom_id = "approve", disabled = False),
                            Button(style = ButtonStyle.grey, emoji = self.bot.get_emoji(929343381409255454), label = f"Sussed by {interaction.user.name}", custom_id = "sus", disabled = True),
                            Button(style = ButtonStyle.red, label = "Ban", custom_id = "ban", disabled = False)]]

        elif interaction.custom_id == "ban":
            try:
                await member.ban(reason="troll in verification")
            except discord.NotFound:
                pass
            await modlog.create_case(self.bot, member.guild, datetime.now(tz = timezone.utc), "ban", member, interaction.user, reason = "troll in verification", until = None, channel = None)
            new_buttons = [[Button(style = ButtonStyle.red, label = f"Banned by {interaction.user.name}", custom_id = "ban", disabled = True)]]

        elif interaction.custom_id == "lock":
            for action_bar in buttons:
                for button in action_bar:
                    if button.id == "lock":
                        button.emoji = "🔒" if str(button.emoji) == "🔓" else "🔓"
                    else:
                        button.disabled = not button.disabled
            await interaction.edit_origin(components = buttons)
            return

        else:
            return

        await interaction.edit_origin(components = new_buttons)



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
                    approved_roles.append(approved_role.id)
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

    @verification_add.command(name = "verifier_roles", require_var_positional=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def verification_add_verifier_roles(self, ctx, roles: commands.Greedy[discord.Role]):
        async with self.config.guild(ctx.guild).verifier_roles() as verifier_roles:
            roles_added = 0
            for verifier_role in roles:
                try:
                    roles_added += 1
                    verifier_roles.append(verifier_role.id)
                except:
                    pass
            await ctx.send(f"Added {roles_added} role(s) to the list of verifier roles!")
        await ctx.tick()

    @verification.command(name = "clear")
    @checks.mod_or_permissions(manage_messages=True)
    async def verification_clear(self, ctx: commands.Context):
        f"Clear roles from the verification settings."
        await self.config.guild(ctx.guild).approved_roles().clear()
        await self.config.guild(ctx.guild).removed_roles().clear()
        await self.config.guild(ctx.guild).banned_roles().clear()
        await self.config.guild(ctx.guild).verifier_roles().clear()
        await self.config.guild(ctx.guild).verifier_channel.set(None)

    @verification_set.command(name = "verifier_channel")
    @checks.mod_or_permissions(manage_messages=True)
    async def verification_set_verifier_channel(self, ctx, channel: discord.TextChannel):
        try:
            await self.config.guild(ctx.guild).verifier_channel.set(channel.id)
        except:
            return
        else:
            await ctx.tick()

    @verification_set.command(name = "approval_channel")
    @checks.mod_or_permissions(manage_messages=True)
    async def verification_set_approval_channel(self, ctx, channel: discord.TextChannel):
        try:
            await self.config.guild(ctx.guild).approval_channel.set(channel.id)
        except:
            return
        else:
            await ctx.tick()

    @verification_set.command(name = "approval_message", aliases = ["welcome_message", "approval_string", "welcome_string"])
    @checks.mod_or_permissions(manage_messages=True)
    async def verification_set_approval_message(self, ctx, *args):
        approval_string = " ".join(args[:])
        await self.config.guild(ctx.guild).approval_message.set(approval_string)
        await ctx.tick()


    @verification.command(name = "show", aliases = ["roles"])
    @checks.mod_or_permissions(manage_messages=True)
    async def verification_show(self, ctx: commands.Context):
            e = discord.Embed(title="", colour=ctx.author.color)
            e.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)

            async with self.config.guild(ctx.guild).approved_roles() as approved_roles:
                if not approved_roles:
                    approved_list = "Empty"
                else:
                    approved_list = ""
                    for role_id in approved_roles:
                        role = discord.utils.get(ctx.guild.roles, id = role_id)
                        if role:
                            approved_list += str(role.name) + ": " + str(role.id) + "\n"

            async with self.config.guild(ctx.guild).sus_roles() as sus_roles:
                if not sus_roles:
                    sus_list = "Empty"
                else:
                    sus_list = ""
                    for role_id in sus_roles:
                        role = discord.utils.get(ctx.guild.roles, id = role_id)
                        if role:
                            sus_list += str(role.name) + ": " + str(role.id) + "\n"

            async with self.config.guild(ctx.guild).verifier_roles() as verifier_roles:
                if not verifier_roles:
                    verifier_list = "Empty"
                else:
                    verifier_list = ""
                    for role_id in verifier_roles:
                        role = discord.utils.get(ctx.guild.roles, id = role_id)
                        if role:
                            verifier_list += str(role.name) + ": " + str(role.id) + "\n"

            async with self.config.guild(ctx.guild).removed_roles() as removed_roles:
                if not removed_roles:
                    removed_list = "Empty"
                else:
                    removed_list = ""
                    for role_id in removed_roles:
                        role = discord.utils.get(ctx.guild.roles, id = role_id)
                        if role:
                            removed_list += str(role.name) + ": " + str(role.id) + "\n"

            approval_channel_id = await self.config.guild(ctx.guild).approval_channel()
            verifier_channel_id = await self.config.guild(ctx.guild).verifier_channel()
            approval_message = await self.config.guild(ctx.guild).approval_message()

            if approval_channel_id is not None:
                approval_channel = discord.utils.get(ctx.guild.channels, id = int(approval_channel_id))
            else:
                approval_channel = "None"

            if verifier_channel_id is not None:
                verifier_channel = discord.utils.get(ctx.guild.channels, id = int(verifier_channel_id))
            else:
                verifier_channel = "None"

            if not approval_message:
                approval_message = "None"

            e.add_field(name="Verifier Channel", value=verifier_channel, inline=False)
            e.add_field(name="Approval Channel", value=approval_channel, inline=False)
            e.add_field(name="Approved Roles", value=approved_list, inline=False)
            e.add_field(name="Sus Roles", value=sus_list, inline=False)
            e.add_field(name="Removed Roles", value=removed_list, inline=False)
            e.add_field(name="Verifier Roles", value=verifier_list, inline=False)
            e.add_field(name="Welcome Message", value=approval_message, inline=False)

            await ctx.send(embed=e)
            await ctx.tick()
