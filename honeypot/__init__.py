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
        exempt_ids = data.get("exempt_roles", [])

        # Build exempt roles display
        exempt_roles = [ctx.guild.get_role(rid) for rid in exempt_ids]
        exempt_roles = [r for r in exempt_roles if r]

        embed = discord.Embed(
            title="Honeypot Configuration",
            color=discord.Color.orange(),
        )

        # Status section
        if channel:
            status = f"**Active** - Monitoring {channel.mention}"
            embed.color = discord.Color.green()
        else:
            status = "**Inactive** - No trap channel configured"
            embed.color = discord.Color.red()

        embed.add_field(name="Status", value=status, inline=False)

        embed.add_field(
            name="Trap Channel",
            value=channel.mention if channel else "*Not set*",
            inline=True,
        )
        embed.add_field(
            name="Log Channel",
            value=log_channel.mention if log_channel else "*Not set*",
            inline=True,
        )

        if exempt_roles:
            role_list = ", ".join(r.mention for r in exempt_roles[:5])
            if len(exempt_roles) > 5:
                role_list += f" *+{len(exempt_roles) - 5} more*"
            embed.add_field(name="Exempt Roles", value=role_list, inline=False)
        else:
            embed.add_field(name="Exempt Roles", value="*None configured*", inline=False)

        # Commands section
        prefix = ctx.clean_prefix
        commands_text = (
            f"`{prefix}honeypot set <channel>` - Set the trap channel\n"
            f"`{prefix}honeypot log [channel]` - Set/clear log channel\n"
            f"`{prefix}honeypot exempt` - View exempt roles\n"
            f"`{prefix}honeypot exempt add <role>` - Add exempt role\n"
            f"`{prefix}honeypot exempt remove <role>` - Remove exempt role"
        )
        embed.add_field(name="Commands", value=commands_text, inline=False)

        embed.set_footer(text="Users who message in the trap channel will be banned automatically.")

        await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())

    @honeypot.command(name="set", aliases=["channel"])
    @commands.admin()
    async def honeypot_set(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set or update the honeypot channel."""
        await self.config.guild(ctx.guild).channel_id.set(channel.id)
        embed = discord.Embed(
            title="Trap Channel Updated",
            description=f"Now monitoring {channel.mention} for intruders.",
            color=discord.Color.green(),
        )
        embed.set_footer(text="Anyone who sends a message there will be banned.")
        await ctx.send(embed=embed)

    @honeypot.command(name="log")
    @commands.admin()
    async def honeypot_log(
        self, ctx: commands.Context, channel: discord.TextChannel = None
    ):
        """Set or clear the honeypot log channel."""
        if channel is None:
            await self.config.guild(ctx.guild).log_channel_id.set(None)
            embed = discord.Embed(
                title="Logging Disabled",
                description="Honeypot events will no longer be logged.",
                color=discord.Color.greyple(),
            )
            await ctx.send(embed=embed)
            return

        await self.config.guild(ctx.guild).log_channel_id.set(channel.id)
        embed = discord.Embed(
            title="Log Channel Updated",
            description=f"Honeypot events will be logged to {channel.mention}.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

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
        prefix = ctx.clean_prefix

        if not exempt_ids:
            embed = discord.Embed(
                title="Exempt Roles",
                description="No roles are exempt from the honeypot.\n\nAll users who message in the trap channel will be banned.",
                color=discord.Color.blue(),
            )
            embed.add_field(
                name="Add Exemptions",
                value=f"`{prefix}honeypot exempt add <role>`",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

        roles = []
        for rid in exempt_ids:
            role = ctx.guild.get_role(rid)
            if role:
                roles.append(role)

        if not roles:
            embed = discord.Embed(
                title="Exempt Roles",
                description="Previously configured roles no longer exist.\n\nYou may want to reconfigure exemptions.",
                color=discord.Color.orange(),
            )
            embed.add_field(
                name="Add Exemptions",
                value=f"`{prefix}honeypot exempt add <role>`",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

        role_list = "\n".join(f"- {role.mention}" for role in roles)
        embed = discord.Embed(
            title="Exempt Roles",
            description=f"These roles can message in the trap channel without being banned:\n\n{role_list}",
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="Manage",
            value=f"`{prefix}honeypot exempt add <role>`\n`{prefix}honeypot exempt remove <role>`",
            inline=False,
        )
        await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())

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
                embed = discord.Embed(
                    title="Already Exempt",
                    description=f"{role.mention} is already on the exemption list.",
                    color=discord.Color.orange(),
                )
                await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
                return
            exempt_ids.append(role.id)

        embed = discord.Embed(
            title="Role Exempted",
            description=f"{role.mention} can now message in the trap channel without being banned.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())

    @honeypot_exempt.command(name="remove")
    @commands.admin()
    async def honeypot_exempt_remove(self, ctx: commands.Context, role: discord.Role):
        """Remove a role from the honeypot exemption list."""
        async with self.config.guild(ctx.guild).exempt_roles() as exempt_ids:
            if role.id not in exempt_ids:
                embed = discord.Embed(
                    title="Not Exempt",
                    description=f"{role.mention} is not on the exemption list.",
                    color=discord.Color.orange(),
                )
                await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
                return
            exempt_ids.remove(role.id)

        embed = discord.Embed(
            title="Role Removed",
            description=f"{role.mention} is no longer exempt from the honeypot.",
            color=discord.Color.red(),
        )
        await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())

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
