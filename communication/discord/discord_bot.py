import os

import discord
from . import logger, DiscordSettings, COGS_DIR
from discord.ext import commands
from .cogs import *


class RaiseBot(commands.Bot):
    def __init__(self, command_prefix,
                 config: DiscordSettings,
                 pubsub: 'PubSub',
                 publish_to: str,
                 subscribe_to: str,
                 creator_username: str,
                 intents
                 ):
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.config = config
        self.pubsub = pubsub
        self.creator_username = creator_username
        self.publish_to = publish_to
        self.subscribe_to = subscribe_to

    async def load_cogs(self, cogs_to_load):
        cogs = [cog for cog in os.listdir(COGS_DIR) if cog.endswith(".py") and (cogs_to_load == "*" or cog[:-3] in cogs_to_load)]

        for cog in cogs:
            cog = f"{COGS_DIR}.{cog[:-3]}"
            await self.load_extension(cog)
            logger.info(f"[RaiseBot/load_cogs] Loaded {cog}")

    async def on_ready(self):
        logger.info(f"[RaiseBot/on_ready] Bot is ready")
        channel = self.get_channel(self.config.bot_chat)
        await channel.send("I'm ready!")
