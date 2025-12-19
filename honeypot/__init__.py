import discord
from redbot.core import commands, Config


class Honeypot(commands.Cog):
    """Automatically bans users who trigger the honeypot channel."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=948372645)
        self.config.register_guild(channel_id=None, exempt_roles=[])

    @commands.admin()
    @commands.command()
    async def honeypot(self, ctx, channel: discord.TextChannel):
        """Set or update the honeypot channel."""
        await self.config.guild(ctx.guild).channel_id.set(channel.id)
        await ctx.send(f"Honeypot channel set to {channel.mention}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        channel_id = await self.config.guild(message.guild).channel_id()
        if not channel_id or message.channel.id != channel_id:
            return

        if await self._is_exempt(message):
            return

        try:
            await message.delete()
        except discord.HTTPException:
            pass

        try:
            await message.guild.ban(
                message.author,
                reason="Triggered honeypot channel",
                delete_message_days=1,
            )
        except discord.HTTPException:
            pass

    async def _is_exempt(self, message: discord.Message) -> bool:
        exempt_role_ids = await self.config.guild(message.guild).exempt_roles()
        if not exempt_role_ids:
            return False

        member = message.guild.get_member(message.author.id)
        if not member:
            return False

        return any(role.id in exempt_role_ids for role in getattr(member, "roles", []))

    async def _send_exempt_list(self, ctx: commands.Context):
        exempt_ids = await self.config.guild(ctx.guild).exempt_roles()
        if not exempt_ids:
            await ctx.send("No roles are currently exempt from the honeypot.")
            return

        roles = []
        for rid in exempt_ids:
            role = ctx.guild.get_role(rid)
            if role:
                roles.append(role)
        if not roles:
            await ctx.send("No valid roles are exempt. You may need to reconfigure them.")
            return

        mentions = ", ".join(role.mention for role in roles)
        await ctx.send(
            "Exempt roles:\n" + mentions,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.group(name="honeypotexempt", aliases=["hpex"], invoke_without_command=True)
    @commands.admin()
    async def honeypot_exempt(self, ctx: commands.Context):
        """Manage honeypot exemption roles."""
        await self._send_exempt_list(ctx)

    @honeypot_exempt.command(name="add")
    @commands.admin()
    async def honeypot_exempt_add(self, ctx: commands.Context, role: discord.Role):
        """Add a role to the honeypot exemption list."""
        async with self.config.guild(ctx.guild).exempt_roles() as exempt_ids:
            if role.id in exempt_ids:
                await ctx.send(f"{role.mention} is already exempt.")
                return
            exempt_ids.append(role.id)

        await ctx.send(f"{role.mention} added to the honeypot exemption list.")

    @honeypot_exempt.command(name="remove")
    @commands.admin()
    async def honeypot_exempt_remove(self, ctx: commands.Context, role: discord.Role):
        """Remove a role from the honeypot exemption list."""
        async with self.config.guild(ctx.guild).exempt_roles() as exempt_ids:
            if role.id not in exempt_ids:
                await ctx.send(f"{role.mention} is not in the exemption list.")
                return
            exempt_ids.remove(role.id)

        await ctx.send(f"{role.mention} removed from the honeypot exemption list.")

    @honeypot_exempt.command(name="list")
    @commands.admin()
    async def honeypot_exempt_list(self, ctx: commands.Context):
        """List honeypot exempt roles."""
        await self._send_exempt_list(ctx)


async def setup(bot):
    await bot.add_cog(Honeypot(bot))
