from redbot.core import commands, Config
import discord

class YetAnotherAutoRoler(commands.Cog):
    """YetAnotherAutoRoler"""

    __version__ = "1.0.0"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        # Thanks Sinbad! And Trusty in whose cogs I found this.
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nVersion: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        pass  # This cog stores no EUD

    def __init__(self):
        self.config = Config.get_conf(self, identifier=3009202134985)
        default_guild = {
            "enabled": False,
            "roles": [],
            "circular_roles": [],
            "index": 0
        }
        self.config.register_guild(**default_guild)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        data = await self.config.guild(member.guild).all()
        if not data["enabled"]:
            return

        if data["circular_roles"]:
            await member.add_roles(member.guild.get_role(data["circular_roles"][(data["index"] % len(data["circular_roles"]))]))

        await member.add_roles(*[member.guild.get_role(role_id) for role_id in data["roles"]])

    @commands.group()
    async def yaar(self, ctx):
        """Autorole commands"""
        pass

    @yaar.group(name="role")
    async def yaar_role(self, ctx):
        """Roles for adding upon user join"""
        pass

    @yaar_role.command(name="add")
    async def yaar_role_add(self, ctx, role: discord.Role):
        """Add a role to be assigned to all new joins"""
        async with self.config.guild(ctx.guild).roles() as roles:
            if role.id in roles:
                await ctx.send("Role already in autorole list")
                return
            roles.append(role.id)
            await ctx.send("{} added to autorole list").format(role.mention)

    @yaar_role.command(name="remove")
    async def yaar_role_remove(self, ctx, role: discord.Role):
        """Remove a role from the autorole list"""
        async with self.config.guild(ctx.guild).roles() as roles:
            if role.id not in roles:
                await ctx.send("Role not in autorole list")
                return
            roles.remove(role.id)
            await ctx.send("{} removed from autorole list").format(role.mention)

    @yaar.group(name="circular")
    async def yaar_circular(self, ctx):
        """Roles to be distributed upon user join"""
        pass

    @yaar_circular.command(name="add")
    async def yaar_circular_add(self, ctx, role: discord.Role):
        """Add a circular role to be distributed to new joins"""
        async with self.config.guild(ctx.guild).circular_roles() as circular_roles:
            if role.id in circular_roles:
                await ctx.send("Role already in circular list")
                return
            circular_roles.append(role.id)
            await ctx.send("{} added to autorole list").format(role.mention)

    @yaar_circular.command(name="remove")
    async def yaar_circular_remove(self, ctx, role: discord.Role):
        """Remove a role from the circular list"""
        async with self.config.guild(ctx.guild).circular_roles() as circular_roles:
            if role.id not in circular_roles:
                await ctx.send("Role not in circular list")
                return
            circular_roles.remove(role.id)
            await ctx.send("{} removed from autorole list").format(role.mention)

    @yaar.command(name="list")
    async def yaar_list(self, ctx):
        """List all roles in the autorole list"""
        e = discord.Embed(title="", colour=ctx.author.color)
        e.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)

        async with self.config.guild(ctx.guild).roles() as roles:
            if not roles:
                role_list = "Empty"
            else:
                role_mentions = [ctx.guild.get_role(role_id).mention for role_id in roles]
                role_list = "\n".join(role_mentions)

        async with self.config.guild(ctx.guild).circular_roles() as circular_roles:
            if not circular_roles:
                circular_list = "Empty"
            else:
                circular_mentions = [ctx.guild.get_role(role_id).mention for role_id in circular_roles]
                role_list = "\n".join(circular_mentions)

        e.add_field(name="Enabled", value=str(await self.config.guild(ctx.guild).enabled()), inline=False)
        e.add_field(name="Autoroles", value=role_list, inline=False)
        e.add_field(name="Circular Roles", value=circular_list, inline=False)

        await ctx.send(embed=e)

    @yaar.command(name="enable")
    async def yaar_enable(self, ctx):
        """Enable autorole"""
        await self.config.guild(ctx.guild).enabled.set(True)
        await ctx.send("AutoRoler enabled")

    @yaar.command(name="disable")
    async def yaar_disable(self, ctx):
        """Disable autorole"""
        await self.config.guild(ctx.guild).enabled.set(False)
        await ctx.send("AutoRoler disabled")
