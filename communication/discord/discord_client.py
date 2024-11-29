import asyncio
from . import BaseInterface, logger, DiscordSettings
from .discord_bot import RaiseBot
import discord
from discord.ext import commands


class DiscordInterface(BaseInterface):
    def __init__(self,
                 token,
                 config: DiscordSettings,
                 pubsub: 'PubSub',
                 publish_to: str,
                 subscribe_to: str,
                 creator_username: str
                 ):

        super().__init__(pubsub)
        self.token = token
        intents = discord.Intents.all()
        self.bot = RaiseBot(command_prefix="!",
                            intents=intents,
                            config=config,
                            publish_to=publish_to,
                            subscribe_to=subscribe_to,
                            creator_username=creator_username,
                            pubsub=pubsub)

    async def initialize(self):
        await self.bot.load_cogs()

    def stop(self):
        pass

    def manage_event_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logger.info('[DiscordInterface/manage_even_loop] Created new event loop')
        return loop

    def run(self):
        try:
            loop = self.manage_event_loop()
            logger.info(f"[DiscordInterface/run] Starting an Application.")
            loop.run_until_complete(self.bot.start(token=self.token))
        except Exception as e:
            logger.exception("[DiscordInterface/run] An error occurred in the bot thread: %s", e)
        finally:
            loop.close()
