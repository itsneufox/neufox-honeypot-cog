import discord
from redbot.core import commands, Config


class Honeypot(commands.Cog):
    """Automatically bans users who trigger the honeypot channel."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=948372645)
        self.config.register_guild(channel_id=None)

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


async def setup(bot):
    await bot.add_cog(Honeypot(bot))
