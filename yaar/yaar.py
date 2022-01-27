from redbot.core import commands, Config, checks
from redbot.core.utils.chat_formatting import humanize_list
import discord

class YetAnotherAutoRoler(commands.Cog):
    """YetAnotherAutoRoler"""

    def format_help_for_context(self, ctx: commands.Context) -> str:
        # Thanks Sinbad! And Trusty in whose cogs I found this.
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nVersion: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        pass  # This cog stores no EUD

    def __init__(self):
        self.config = Config.get_conf(self, identifier=3009202134985)
        default_guild = {"enabled": False, "roles": [], "circular_roles": [], "index": 0}
        self.config.register_guild(**default_guild)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        data = await self.config.guild(member.guild).all()
        if not data["enabled"]:
            return

        if data["circular_roles"]:
            await member.add_roles(member.guild.get_role(data["circular_roles"][(data["index"] % len(data["circular_roles"]))]))
            await self.config.guild(member.guild).index.set(data["index"] + 1)

        await member.add_roles(*[member.guild.get_role(role_id) for role_id in data["roles"]])

    @commands.group(alias="yetanotherautoroler")
    @checks.mod_or_permissions(manage_roles=True)
    async def yaar(self, ctx):
        """YetAnotherAutoRoler commands"""
        pass

    @yaar.group(name="role")
    async def yaar_role(self, ctx):
        """Roles to be added upon user join"""
        pass

    @yaar_role.command(name="add", require_var_positional=True)
    async def yaar_role_add(self, ctx, *roles: discord.Role):
        """Add role(s) to be assigned to all new joins"""
        async with self.config.guild(ctx.guild).roles() as autoroles:
            roles_added = [role.id for role in roles if role.id not in autoroles]
            autoroles.extend(roles_added)

            if not roles_added:
                await ctx.send("Role(s) already in autorole list")
                return

            await ctx.send(f"Added {humanize_list([ctx.guild.get_role(role_id).mention for role_id in roles_added])} to autorole list")

    @yaar_role.command(name="remove", require_var_positional=True)
    async def yaar_role_remove(self, ctx, *roles: discord.Role):
        """Remove role(s) from the autorole list"""
        async with self.config.guild(ctx.guild).roles() as autoroles:
            roles_removed = [role.id for role in roles if role.id in autoroles]

            if not roles_removed:
                await ctx.send("Role(s) not in autorole list")
                return

            for role in roles_removed:
                autoroles.remove(role)

            await ctx.send(f"Removed {humanize_list([ctx.guild.get_role(role_id).mention for role_id in roles_removed])} from autorole list")

    @yaar.group(name="circular")
    async def yaar_circular(self, ctx):
        """Circular roles to be distributed to users"""
        pass

    @yaar_circular.command(name="add", require_var_positional=True)
    async def yaar_circular_add(self, ctx, *roles: discord.Role):
        """Add circular role(s) to be distributed to new joins"""
        async with self.config.guild(ctx.guild).circular_roles() as circular_roles:
            roles_added = [role.id for role in roles if role.id not in circular_roles]
            circular_roles.extend(roles_added)

            if not roles_added:
                await ctx.send("Role(s) already in circular list")
                return

            await ctx.send(f"Added {humanize_list([ctx.guild.get_role(role_id).mention for role_id in roles_added])} to circular list")

    @yaar_circular.command(name="remove", require_var_positional=True)
    async def yaar_circular_remove(self, ctx, *roles: discord.Role):
        """Remove role(s) from the circular list"""
        async with self.config.guild(ctx.guild).circular_roles() as circular_roles:
            roles_removed = [role.id for role in roles if role.id in circular_roles]

            if not roles_removed:
                await ctx.send("Role(s) not in circular list")
                return

            for role in roles_removed:
                circular_roles.remove(role)

            await ctx.send(f"Removed {humanize_list([ctx.guild.get_role(role_id).mention for role_id in roles_removed])} from circular list")

    @yaar.command(name="list")
    async def yaar_list(self, ctx):
        """List all roles in the autorole list"""
        e = discord.Embed(title="", colour=ctx.author.color)
        e.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)

        async with self.config.guild(ctx.guild).roles() as roles:
            if not roles:
                role_list = "Empty"
            else:
                role_mentions = [ctx.guild.get_role(role_id) for role_id in roles]
                role_list = "\n".join(role.mention for role in role_mentions if role is not None)

        async with self.config.guild(ctx.guild).circular_roles() as circular_roles:
            if not circular_roles:
                circular_list = "Empty"
            else:
                circular_mentions = [ctx.guild.get_role(role_id) for role_id in circular_roles]
                circular_list = "\n".join(role.mention for role in circular_mentions if role is not None)

        e.add_field(name="Enabled", value=str(await self.config.guild(ctx.guild).enabled()), inline=False)
        e.add_field(name="Autoroles", value=role_list, inline=False)
        e.add_field(name="Circular Roles", value=circular_list, inline=False)

        await ctx.send(embed=e)

    @yaar.command(name="enable")
    async def yaar_enable(self, ctx: commands.Context, toggle: bool):
        """Toggle autoembedding in this guild.

        This is disabled by default."""
        await self.config.guild(ctx.guild).enabled.set(toggle)
        await ctx.send(f"YetAnotherAutoRoler has been turned {'on' if toggle else 'off'}.")
