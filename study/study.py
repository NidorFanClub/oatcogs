from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
import asyncio
import discord.utils 
import discord
import os
import typing

class Study(commands.Cog):
    """Study stuff!"""
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=13121312, force_registration=True)
        self.config.register_member(cached_roles = [], study_in_progress = False, locked = False)
        self.config.register_guild(exempt_roles = [], study_role = "", banned_roles = [])

    @commands.group(autohelp=False)
    @commands.guild_only()
    async def study(self, ctx, member: typing.Optional[discord.Member]):
        """Temporary time-out for those who lack self control."""
        if not ctx.invoked_subcommand:
            if not member or not ctx.author.guild_permissions.administrator:
                member = ctx.author

            banned_role_ids = await self.config.guild(ctx.guild).banned_roles()
            exempt_role_ids = await self.config.guild(ctx.guild).exempt_roles()
            study_role_id = await self.config.guild(ctx.guild).study_role()

            if not study_role_id:
                return

            study_role = discord.utils.get(ctx.guild.roles, id=study_role_id)

            async with self.config.member(member).cached_roles() as cached_roles:
                for banned_role_id in banned_role_ids:
                    banned_role = discord.utils.get(ctx.guild.roles, id=banned_role_id)
                    if banned_role in member.roles:
                        return

                if await self.config.member(member).study_in_progress() and study_role not in member.roles:
                    return

                if await self.config.member(member).study_in_progress():
                    current_user_roles = member.roles
                    cached_user_roles = []

                    for role_id in cached_roles:
                        role = discord.utils.get(ctx.guild.roles, id=role_id)
                        if role and role not in cached_user_roles:
                            cached_user_roles.append(role)

                    user_roles = current_user_roles + [i for i in cached_user_roles if i not in current_user_roles]

                    try:
                        await member.edit(roles=user_roles)
                    except:
                        #to do: add role react on fail
                        pass
                    else:
                        cached_roles.clear()
                        await member.remove_roles(study_role, atomic=True)
                        await self.config.member(member).study_in_progress.set(False)
                        await ctx.tick()

                else:
                    current_user_roles = member.roles
                    exempt_user_roles = []

                    for role in member.roles:
                        if role.id in exempt_role_ids:
                            exempt_user_roles.append(role)
                        else:
                            cached_roles.append(role.id)

                    try:
                        await member.edit(roles=exempt_user_roles)
                    except:
                        #to do: add role react on fail
                        pass
                    else:
                        await member.add_roles(study_role, atomic=True)
                        await self.config.member(member).study_in_progress.set(True)
                        await ctx.react_quietly("📝")


    @study.group(name = "Krik")
    @checks.mod_or_permissions(manage_messages=True)
    async def study_krik(self, ctx: commands.Context) -> None:
        f"test for precedence."
        pass

    @study.group(name = "set")
    @checks.mod_or_permissions(manage_messages=True)
    async def study_set(self, ctx: commands.Context) -> None:
        f"Settings for study."
        pass
        
    @study_set.group(name = "show", aliases = ["output", "display", "get"])
    @checks.mod_or_permissions(manage_messages=True)
    async def study_set_show(self, ctx: commands.Context) -> None:
        f"Display study settings and debug info."
        pass

    @study_set_show.command(name = "user", aliases = ["member"])
    @checks.mod_or_permissions(manage_messages=True)
    async def study_set_show_user(self, ctx: commands.Context, member: typing.Optional[discord.Member]):
        if not member:
            member = ctx.author

        e = discord.Embed(title="", colour=member.color)
        e.set_author(name=member, icon_url=member.avatar_url)

        current_role_list = ""
        cached_role_list = ""

        if not member.roles:
            current_role_list = "No current roles"
        else:
            for role in member.roles:
                if role:
                    current_role_list += str(role.name) + ": " + str(role.id) + "\n"

        async with self.config.member(member).cached_roles() as cached_roles:
            if not cached_roles:
                cached_role_list = "No cached roles"
            else:
                for role_id in cached_roles:
                    role = discord.utils.get(ctx.guild.roles, id = role_id)
                    if role:
                        cached_role_list += str(role.name) + ": " + str(role.id) + "\n"

        studying = await self.config.member(member).study_in_progress()

        e.add_field(name="Current Roles", value=current_role_list, inline=False)
        e.add_field(name="Stored Roles", value=cached_role_list, inline=False)
        e.add_field(name="Study Boolean", value=studying, inline=False)

        await ctx.send(embed=e)
        await ctx.tick()

    @study_set_show.command(name = "settings", aliases = ["roles"])
    @checks.mod_or_permissions(manage_messages=True)
    async def study_set_show_settings(self, ctx: commands.Context):
            e = discord.Embed(title="", colour=ctx.author.color)
            e.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)

            study_list = ""
            exempt_list = ""
            ban_list = ""

            async with self.config.guild(ctx.guild).exempt_roles() as exempt_roles:
                if not exempt_roles:
                    exempt_list = "Empty"
                else:
                    for exempt_role_id in exempt_roles:
                        exempt_role = discord.utils.get(ctx.guild.roles, id = exempt_role_id)
                        if exempt_role:
                            exempt_list += str(exempt_role.name) + ": " + str(exempt_role.id) + "\n"

            async with self.config.guild(ctx.guild).banned_roles() as banned_roles:
                if not banned_roles:
                    ban_list = "Empty"
                else:
                    for banned_role_id in banned_roles:
                        banned_role = discord.utils.get(ctx.guild.roles, id = banned_role_id)
                        if banned_role:
                            ban_list += str(banned_role.name) + ": " + str(banned_role.id) + "\n"

            study_role_id = await self.config.guild(ctx.guild).study_role()
            study_role = discord.utils.get(ctx.guild.roles, id = study_role_id)
            study_list = str(study_role.name) + ": " + str(study_role.id) + "\n"

            e.add_field(name="Study Role", value=study_list, inline=False)
            e.add_field(name="Exempt Roles", value=exempt_list, inline=False)
            e.add_field(name="Banned Roles", value=ban_list, inline=False)

            await ctx.send(embed=e)
            await ctx.tick()

    @study_set.group(name = "add")
    @checks.mod_or_permissions(manage_messages=True)
    async def study_set_add(self, ctx: commands.Context) -> None:
        f"Add roles to the study settings."
        pass

    @study_set_add.command(name = "study", aliases = ["study_role", "studyrole"])
    @checks.mod_or_permissions(manage_messages=True)
    async def study_set_add_study(self, ctx, role: discord.Role):
        await self.config.guild(ctx.guild).study_role.set(role.id)
        await ctx.tick()

    @study_set_add.command(name = "banned", aliases = ["banned_role", "bannedrole"], require_var_positional=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def study_set_add_banned(self, ctx, roles: commands.Greedy[discord.Role]):
        async with self.config.guild(ctx.guild).banned_roles() as banned_roles:
            roles_added = 0
            for banned_role in roles:
                try:
                    roles_added += 1
                    banned_roles.append(banned_role.id)
                except:
                    pass
            await ctx.send(f"Added {roles_added} role(s) to the list of banned roles!")
        await ctx.tick()

    @study_set_add.command(name = "exempt", aliases = ["exempt_role", "exemptrole"], require_var_positional=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def study_set_add_exempt(self, ctx, roles: commands.Greedy[discord.Role]):

        async with self.config.guild(ctx.guild).exempt_roles() as exempt_roles:
            roles_added = 0
            for exempt_role in roles:
                try:
                    roles_added += 1
                    exempt_roles.append(exempt_role.id)
                except:
                    pass
            await ctx.send(f"Added {roles_added} role(s) to the list of exempt roles!")
        await ctx.tick()

    @study_set.group(name = "remove", aliases = ["delete", "del", "rem"])
    @checks.mod_or_permissions(manage_messages=True)
    async def study_set_remove(self, ctx: commands.Context) -> None:
        f"Remove roles from the study settings."
        pass

    @study_set_remove.command(name = "study", aliases = ["study_role", "studyrole"])
    @checks.mod_or_permissions(manage_messages=True)
    async def study_set_remove_study(self, ctx, role: discord.Role):
        await self.config.guild(ctx.guild).study_role.set("")
        await ctx.tick()


    @study_set_remove.command(name = "banned", aliases = ["banned_role", "bannedrole"], require_var_positional=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def study_set_remove_banned(self, ctx, roles: commands.Greedy[discord.Role]):
        async with self.config.guild(ctx.guild).banned_roles() as banned_roles:
            roles_removed = 0
            for banned_role in roles:
                try:
                    roles_removed += 1
                    banned_roles.remove(banned_role.id)
                except:
                    pass
            await ctx.send(f"Removed {roles_removed} role(s) from the list of banned roles!")
        await ctx.tick()
            
    @study_set_remove.command(name = "exempt", aliases = ["exempt_role", "exemptrole"], require_var_positional=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def study_set_remove_exempt(self, ctx, roles: commands.Greedy[discord.Role]):
        async with self.config.guild(ctx.guild).exempt_roles() as exempt_roles:
            roles_removed = 0
            for exempt_role in roles:
                try:
                    roles_removed += 1
                    exempt_roles.remove(exempt_role.id)
                except:
                    pass
            await ctx.send(f"Removed {roles_removed} role(s) from the list of exempt roles!")
        await ctx.tick()

    @study_set.group(name = "clear", aliases = ["wipe"])
    @checks.mod_or_permissions(manage_messages=True)
    async def study_set_clear(self, ctx: commands.Context) -> None:
        f"Clear data from the study settings."
        pass

    @study_set_clear.command(name = "exempt", aliases = ["exempt_roles", "exemptroles"])
    @checks.mod_or_permissions(manage_messages=True)
    async def study_set_clear_exempt(self, ctx):
        async with self.config.guild(ctx.guild).exempt_roles() as exempt_roles:
            exempt_roles.clear()
        await ctx.tick()

    @study_set_clear.command(name = "banned", aliases = ["banned_roles", "bannedroles"])
    @checks.mod_or_permissions(manage_messages=True)
    async def study_set_clear_banned(self, ctx):
        async with self.config.guild(ctx.guild).banned_roles() as banned_roles:
            banned_roles.clear()
        await ctx.tick()

    @study_set.command(name = "reset")
    @checks.mod_or_permissions(manage_messages=True)
    async def study_set_reset(self, ctx, member: typing.Optional[discord.Member]):
        if not member:
            member = ctx.author
        await self.config.member(member).study_in_progress.set(False)
        async with self.config.member(member).cached_roles() as cached_roles:
            cached_roles.clear()
        await ctx.tick()
