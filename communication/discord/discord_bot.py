import asyncio
from . import BaseInterface, logger, DiscordSettings
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
        self.CREATOR_ID = config.creator_id
        self.CREATOR_USERNAME = creator_username
        self.publish_to = publish_to
        self.subscribe_to = subscribe_to
        self.token = token
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        self.client = commands.Bot(command_prefix="!", intents=intents, heartbeat_interval=60.0)

    def initialize(self):
        pass

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
            self.initialize()
            logger.info(f"[DiscordInterface/run] Starting an Application.")
            loop.run_until_complete(self.client.run(token=self.token))
        except Exception as e:
            logger.exception("An error occurred in the bot thread: %s", e)
