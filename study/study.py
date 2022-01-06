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
        self.config.register_member(roles = [], study_in_progress = False)
        self.config.register_guild(exempt_roles = [], study_role = "", banned_roles = [])

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def study(self, ctx):
        """Temporary time-out for those who lack self control."""

        banned_role_ids = await self.config.guild(ctx.guild).banned_roles()
        exempt_role_ids = await self.config.guild(ctx.guild).exempt_roles()
        study_role_id = await self.config.guild(ctx.guild).study_role()

        if not study_role_id:
            return

        if ctx.message.guild is None:
            return

        if await self.bot.cog_disabled_in_guild(self, ctx.message.guild):
            return

        valid_user = isinstance(ctx.message.author, discord.Member) and not ctx.message.author.bot

        if not valid_user:
            return

        if await self.bot.is_automod_immune(ctx.message):
            return

        study_role = discord.utils.get(ctx.guild.roles, id=study_role_id)

        async with self.config.member(ctx.author).roles() as roles:
            for banned_role_id in banned_role_ids:
                banned_role = discord.utils.get(ctx.guild.roles, id=banned_role_id)
                if banned_role in ctx.author.roles:
                    return

            if await self.config.member(ctx.author).study_in_progress() and study_role not in ctx.author.roles:
                return

            if await self.config.member(ctx.author).study_in_progress():
                new_roles = []

                for role_id in roles:
                    role = discord.utils.get(ctx.guild.roles, id=role_id)
                    if role:
                        new_roles.append(role)

                for exempt_role_id in exempt_role_ids:
                    exempt_role = discord.utils.get(ctx.guild.roles, id=exempt_role_id)
                    if exempt_role in ctx.author.roles:
                        new_roles.append(exempt_role)

                await ctx.author.edit(roles=new_roles)
                await ctx.author.remove_roles(study_role)
                await self.config.member(ctx.author).study_in_progress.set(False)
                await ctx.tick()

            else:
                user_exempt_roles = []
                user_roles = []

                for role in ctx.author.roles:
                    if role.id not in exempt_role_ids:
                        user_roles.append(role.id)
                    else:
                        user_exempt_roles.append(role)

                if user_exempt_roles:
                    try:
                        await ctx.author.edit(roles=user_exempt_roles)
                    except:
                        pass

                try:
                    roles = user_roles
                except:
                    return
                else:
                    await ctx.author.add_roles(study_role)
                    await self.config.member(ctx.author).study_in_progress.set(True)
                    await ctx.react_quietly("📝")
                
    @checks.mod_or_permissions(manage_messages=True)
    @commands.command()
    async def arbitration(self, ctx: commands.Context, member: typing.Optional[discord.Member]):
        banned_role_ids = await self.config.guild(ctx.guild).banned_roles()
        exempt_role_ids = await self.config.guild(ctx.guild).exempt_roles()
        study_role_id = await self.config.guild(ctx.guild).study_role()

        if not banned_role_ids:
            return

        if ctx.message.guild is None:
            return

        if await self.bot.cog_disabled_in_guild(self, ctx.message.guild):
            return

        valid_user = isinstance(ctx.message.author, discord.Member) and not ctx.message.author.bot

        if not valid_user:
            return

        if await self.bot.is_automod_immune(ctx.message):
            return

        try:
            study_role = discord.utils.get(ctx.guild.roles, id=study_role_id)
        except:
            pass

        new_roles = []

        async with self.config.member(member).roles() as roles:
            for banned_role_id in banned_role_ids:
                banned_role = discord.utils.get(ctx.guild.roles, id=banned_role_id)

                if banned_role in member.roles:
                    for role_id in roles:
                        role = discord.utils.get(ctx.guild.roles, id=role_id)
                        if role:
                            new_roles.append(role)

                    for exempt_role_id in exempt_role_ids:
                        if exempt_role_id in member.roles:
                            exempt_role = discord.utils.get(ctx.guild.roles, id=exempt_role_id)
                            if exempt_role:
                                new_roles.append(exempt_role)

                    await member.edit(roles=new_roles)
                    await member.remove_roles(banned_role)
                    await ctx.tick()
                else:
                    try:
                        if study_role in member.roles:
                            await member.remove_roles(study_role)
                    except:
                        pass

                    user_exempt_roles = []
                    user_roles = []

                    for role in member.roles:
                        if role.id not in exempt_role_ids:
                            user_roles.append(role.id)
                        else:
                            user_exempt_roles.append(role)

                    if user_exempt_roles:
                        try:
                            await member.edit(roles=user_exempt_roles)
                        except:
                            pass

                    try:
                        roles = user_roles
                    except:
                        return
                    else:
                        await member.add_roles(discord.utils.get(ctx.guild.roles, id=banned_role_ids[0]))
                        await self.config.member(member).study_in_progress.set(False)
                        await ctx.react_quietly("🚔")
                     
    @commands.group(autohelp=True)
    @commands.guild_only()
    async def studyset(self, ctx: commands.Context):
        f"Settings for study."
        
    @checks.mod_or_permissions(manage_messages=True)
    @studyset.command(name = "showuser")
    async def studyset_showuser(self, ctx: commands.Context, member: typing.Optional[discord.Member]):
        if not member:
            member = ctx.author

        e = discord.Embed(title="", colour=member.color)
        e.set_author(name=member, icon_url=member.avatar_url)

        current_role_list = ""
        cached_role_list = ""

        if not ctx.author.roles:
            current_role_list = "No current roles"
        else:
            for role in ctx.author.roles:
                if role:
                    current_role_list += str(role.name) + ": " + str(role.id) + "\n"

        async with self.config.member(member).roles() as roles:
            if not roles:
                cached_role_list = "No cached roles"
            else:
                for role_id in roles:
                    role = discord.utils.get(ctx.guild.roles, id = role_id)
                    if role:
                        cached_role_list += str(role.name) + ": " + str(role.id) + "\n"

        studying = await self.config.member(member).study_in_progress()

        e.add_field(name="Current Roles", value=current_role_list, inline=False)
        e.add_field(name="Stored Roles", value=cached_role_list, inline=False)
        e.add_field(name="Study Boolean", value=studying, inline=False)

        await ctx.send(embed=e)
        await ctx.tick()
            
    @checks.mod_or_permissions(manage_messages=True)
    @studyset.command(name = "reset")
    async def studyset_reset(self, ctx, member: typing.Optional[discord.Member]):
        if not member:
            member = ctx.author
        await self.config.member(member).study_in_progress.set(False)
        async with self.config.member(member).roles() as roles:
            roles.clear()
        await ctx.tick()

    @checks.mod_or_permissions(manage_messages=True)
    @studyset.command(name = "addstudyrole")
    async def studyset_studyrole(self, ctx, role: discord.Role):
        await self.config.guild(ctx.guild).study_role.set(role.id)
        await ctx.tick()

    @checks.mod_or_permissions(manage_messages=True)
    @studyset.command(name = "removestudyrole")
    async def studyset_removestudyrole(self, ctx, role: discord.Role):
        await self.config.guild(ctx.guild).study_role.set("")
        await ctx.tick()

    @checks.mod_or_permissions(manage_messages=True)
    @studyset.command(name = "addbannedrole")
    async def studyset_addbannedrole(self, ctx, roles: commands.Greedy[discord.Role]):
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

    @checks.mod_or_permissions(manage_messages=True)
    @studyset.command(name = "removebannedrole")
    async def studyset_removebannedrole(self, ctx, roles: commands.Greedy[discord.Role]):
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

    @checks.mod_or_permissions(manage_messages=True)
    @studyset.command(name = "addexemptrole")
    async def studyset_addexemptrole(self, ctx, roles: commands.Greedy[discord.Role]):
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
            
    @checks.mod_or_permissions(manage_messages=True)
    @studyset.command(name = "removeexemptrole")
    async def studyset_removeexemptrole(self, ctx, roles: commands.Greedy[discord.Role]):
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
            
    @checks.mod_or_permissions(manage_messages=True)
    @studyset.command(name = "clearexempt")
    async def studyset_clearexempt(self, ctx):
        async with self.config.guild(ctx.guild).exempt_roles() as exempt_roles:
            exempt_roles.clear()
        await ctx.tick()

    @checks.mod_or_permissions(manage_messages=True)
    @studyset.command(name = "clearbanned")
    async def studyset_clearbanned(self, ctx):
        async with self.config.guild(ctx.guild).banned_roles() as banned_roles:
            banned_roles.clear()
        await ctx.tick()

    @checks.mod_or_permissions(manage_messages=True)
    @studyset.command(name = "showsettings")
    async def studyset_showsettings(self, ctx: commands.Context):
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
