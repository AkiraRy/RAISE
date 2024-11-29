import discord
from discord.ext import commands


class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        pass

    @commands.command(name="ping")
    async def ping_command(self, ctx: commands.Context):
        await ctx.send("Pong!")

    @discord.app_commands.command(name="ping", description="Get various pieces of valuable knowledge!")
    async def command(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"Pong!")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Ping(bot))