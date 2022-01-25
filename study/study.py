from redbot.core import commands, Config, checks
from redbot.core.utils.chat_formatting import humanize_list
import asyncio
import discord.utils
import discord
import typing

class Study(commands.Cog):
    """Study stuff!"""
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=13121312, force_registration=True)
        self.config.register_member(cached_roles = [], study_in_progress = False, locked = False)
        self.config.register_guild(exempt_roles = [], study_role = "", banned_roles = [])

    @commands.command(aliases = ["unstudy"])
    @commands.guild_only()
    async def study(self, ctx):
        """Temporary time-out for those who lack self control."""
        member = ctx.author

        banned_role_ids = await self.config.guild(ctx.guild).banned_roles()
        exempt_role_ids = await self.config.guild(ctx.guild).exempt_roles()
        study_role_id = await self.config.guild(ctx.guild).study_role()

        locked = await self.config.member(member).locked()

        if not study_role_id or locked:
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
                    await self.config.member(member).locked.set(False)
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
                    await self.config.member(member).locked.set(False)
                    await ctx.react_quietly("📝")

    @commands.group(name = "studyset")
    @checks.mod_or_permissions(manage_roles=True)
    async def studyset(self, ctx: commands.Context) -> None:
        f"Settings for the study cog."
        pass

    @studyset.group(name = "add")
    async def studyset_add(self, ctx: commands.Context) -> None:
        f"Add roles to the study settings."
        pass

    @studyset_add.command(name = "study", aliases = ["study_role", "studyrole"])
    async def studyset_add_study(self, ctx, role: discord.Role):
        await self.config.guild(ctx.guild).study_role.set(role.id)
        await ctx.send(f"Set {role.mention} as study role")

    @studyset_add.command(name = "banned", aliases = ["banned_role", "bannedrole"], require_var_positional=True)
    async def studyset_add_banned(self, ctx, *roles: discord.Role):
        async with self.config.guild(ctx.guild).banned_roles() as banned_roles:
            roles_added = [role.id for role in roles if role.id not in banned_roles]
            banned_roles.extend(roles_added)

            if not roles_added:
                await ctx.send("Role(s) already in banned role list")
                return

            await ctx.send(f"Added {humanize_list([ctx.guild.get_role(role_id).mention for role_id in roles_added])} to banned role list")

    @studyset_add.command(name = "exempt", aliases = ["exempt_role", "exemptrole"], require_var_positional=True)
    async def studyset_add_exempt(self, ctx, *roles: discord.Role):
        async with self.config.guild(ctx.guild).exempt_roles() as exempt_roles:
            roles_added = [role.id for role in roles if role.id not in exempt_roles]
            exempt_roles.extend(roles_added)

            if not roles_added:
                await ctx.send("Role(s) already in exempt role list")
                return

            await ctx.send(f"Added {humanize_list([ctx.guild.get_role(role_id).mention for role_id in roles_added])} to exempt role list")

    @studyset.group(name = "remove", aliases = ["delete", "del", "rem"])
    async def studyset_remove(self, ctx: commands.Context) -> None:
        f"Remove roles from the study settings."
        pass

    @studyset_remove.command(name = "study", aliases = ["study_role", "studyrole"])
    async def studyset_remove_study(self, ctx, role: discord.Role):
        await self.config.guild(ctx.guild).study_role.set("")
        await ctx.send(f"Removed study role")


    @studyset_remove.command(name = "banned", aliases = ["banned_role", "bannedrole"], require_var_positional=True)
    async def studyset_remove_banned(self, ctx, *roles: discord.Role):
        async with self.config.guild(ctx.guild).banned_roles() as banned_roles:
            roles_removed = [role.id for role in roles if role.id in banned_roles]

            if not roles_removed:
                await ctx.send("Role(s) not in banned role list")
                return

            for role in roles_removed:
                banned_roles.remove(role)

            await ctx.send(f"Removed {humanize_list([ctx.guild.get_role(role_id).mention for role_id in roles_removed])} from banned role list")

    @studyset_remove.command(name = "exempt", aliases = ["exempt_role", "exemptrole"], require_var_positional=True)
    async def studyset_remove_exempt(self, ctx, *roles: discord.Role):
        async with self.config.guild(ctx.guild).exempt_roles() as exempt_roles:
            roles_removed = [role.id for role in roles if role.id in exempt_roles]

            if not roles_removed:
                await ctx.send("Role(s) not in exempt role list")
                return

            for role in roles_removed:
                exempt_roles.remove(role)

            await ctx.send(f"Removed {humanize_list([ctx.guild.get_role(role_id).mention for role_id in roles_removed])} from exempt role list")

    @studyset.group(name = "clear", aliases = ["wipe"])
    async def studyset_clear(self, ctx: commands.Context) -> None:
        f"Clear data from the study settings."
        pass

    @studyset_clear.command(name = "banned", aliases = ["banned_roles", "bannedroles"])
    async def studyset_clear_banned(self, ctx):
        async with self.config.guild(ctx.guild).banned_roles() as banned_roles:
            banned_roles.clear()
        await ctx.tick()

    @studyset_clear.command(name = "exempt", aliases = ["exempt_roles", "exemptroles"])
    async def studyset_clear_exempt(self, ctx):
        async with self.config.guild(ctx.guild).exempt_roles() as exempt_roles:
            exempt_roles.clear()
        await ctx.tick()

    @studyset.command(name = "list", aliases = ["output", "display", "get", "show"])
    async def studyset_list(self, ctx: commands.Context) -> None:
        e = discord.Embed(title="", colour=ctx.author.color)
        e.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)

        study_list = ""
        exempt_list = ""
        banned_list = ""

        async with self.config.guild(ctx.guild).exempt_roles() as exempt_roles:
            if not exempt_roles:
                exempt_list = "Empty"
            else:
                role_mentions = [ctx.guild.get_role(role_id).mention for role_id in exempt_roles]
                exempt_list = "\n".join(role_mentions)

        async with self.config.guild(ctx.guild).banned_roles() as banned_roles:
            if not banned_roles:
                banned_list = "Empty"
            else:
                role_mentions = [ctx.guild.get_role(role_id).mention for role_id in banned_roles]
                banned_list = "\n".join(role_mentions)

        study_mention = ctx.guild.get_role(await self.config.guild(ctx.guild).study_role()).mention
        study_list = study_mention

        e.add_field(name="Study Role", value=study_list, inline=False)
        e.add_field(name="Exempt Roles", value=exempt_list, inline=False)
        e.add_field(name="Banned Roles", value=banned_list, inline=False)

        await ctx.send(embed=e)
        await ctx.tick()

    @studyset.command(name = "user", aliases = ["member"])
    async def studyset_user(self, ctx: commands.Context, member: typing.Optional[discord.Member]):
        if not member:
            member = ctx.author

        e = discord.Embed(title="", colour=member.color)
        e.set_author(name=member, icon_url=member.avatar_url)

        current_role_list = ""
        cached_role_list = ""

        if not member.roles:
            current_role_list = "No current roles"
        else:
            cached_role_list = "\n".join(member.roles)

        async with self.config.member(member).cached_roles() as cached_roles:
            if not cached_roles:
                cached_role_list = "No cached roles"
            else:
                role_mentions = [ctx.guild.get_role(role_id).mention for role_id in cached_roles]
                cached_role_list = "\n".join(role_mentions)

        studying = await self.config.member(member).study_in_progress()

        e.add_field(name="Current Roles", value=current_role_list, inline=False)
        e.add_field(name="Stored Roles", value=cached_role_list, inline=False)
        e.add_field(name="Study Boolean", value=studying, inline=False)

        await ctx.send(embed=e)
        await ctx.tick()

    @studyset.command(name = "reset")
    async def studyset_reset(self, ctx, member: typing.Optional[discord.Member]):
        if not member:
            member = ctx.author
        await self.config.member(member).study_in_progress.set(False)
        async with self.config.member(member).cached_roles() as cached_roles:
            cached_roles.clear()
        await ctx.tick()

    @studyset.command(name = "lock")
    async def studyset_lock(self, ctx):
        pass

    @studyset.command(name = "unlock")
    async def studyset_unlock(self, ctx):
        pass
