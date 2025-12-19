import discord
from redbot.core import commands, Config


class Honeypot(commands.Cog):
    """Automatically bans users who trigger the honeypot channel."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=948372645)
        self.config.register_guild(
            channel_id=None,
            exempt_roles=[],
            log_channel_id=None,
        )

    @commands.group(name="honeypot", invoke_without_command=True)
    @commands.admin()
    async def honeypot(self, ctx: commands.Context):
        """Manage honeypot settings."""
        data = await self.config.guild(ctx.guild).all()
        channel = ctx.guild.get_channel(data.get("channel_id"))
        log_channel = ctx.guild.get_channel(data.get("log_channel_id"))
        exempt_count = len(data.get("exempt_roles", []))

        lines = [
            f"Honeypot channel: {channel.mention if channel else 'Not set'}",
            f"Log channel: {log_channel.mention if log_channel else 'Not set'}",
            f"Exempt roles: {exempt_count}",
            "",
            "Use subcommands: set, log, exempt.",
        ]
        await ctx.send("\n".join(lines))

    @honeypot.command(name="set", aliases=["channel"])
    @commands.admin()
    async def honeypot_set(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set or update the honeypot channel."""
        await self.config.guild(ctx.guild).channel_id.set(channel.id)
        await ctx.send(f"Honeypot channel set to {channel.mention}")

    @honeypot.command(name="log")
    @commands.admin()
    async def honeypot_log(
        self, ctx: commands.Context, channel: discord.TextChannel = None
    ):
        """Set or clear the honeypot log channel."""
        if channel is None:
            await self.config.guild(ctx.guild).log_channel_id.set(None)
            await ctx.send("Honeypot logging disabled.")
            return

        await self.config.guild(ctx.guild).log_channel_id.set(channel.id)
        await ctx.send(f"Honeypot logs will be sent to {channel.mention}.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        channel_id = await self.config.guild(message.guild).channel_id()
        if not channel_id or message.channel.id != channel_id:
            return

        exempt = await self._is_exempt(message)
        if exempt:
            await self._send_log(
                message.guild,
                f"{message.author} was exempt from the honeypot in {message.channel.mention}.",
            )
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
            await self._send_log(
                message.guild,
                f"{message.author} was banned for tripping the honeypot in {message.channel.mention}.",
                target=message.author,
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

    @honeypot.group(name="exempt", aliases=["ex"], invoke_without_command=True)
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

    async def _send_log(
        self,
        guild: discord.Guild,
        description: str,
        *,
        target: discord.abc.User = None,
    ):
        log_channel_id = await self.config.guild(guild).log_channel_id()
        if not log_channel_id:
            return

        channel = guild.get_channel(log_channel_id)
        if not channel or not isinstance(channel, discord.TextChannel):
            return

        embed = discord.Embed(description=description, color=discord.Color.red())
        embed.timestamp = discord.utils.utcnow()
        author_name = str(target) if target else "Honeypot Alert"
        icon_url = None
        if target and hasattr(target, "display_avatar"):
            icon_url = target.display_avatar.url
        elif guild.me and guild.me.display_avatar:
            icon_url = guild.me.display_avatar.url

        embed.set_author(name=author_name, icon_url=icon_url)
        embed.set_footer(text=f"Guild: {guild.name}")

        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            return


async def setup(bot):
    await bot.add_cog(Honeypot(bot))
