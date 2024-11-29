import os
import sys
import traceback

import discord
from . import logger, DiscordSettings, COGS_DIR
from discord.ext import commands
from .cogs import cogs


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

    async def load_cogs(self):
        for cog in cogs:
            await self.load_extension(cog)
            logger.info(f"[RaiseBot/load_cogs] Loaded {cog}")

    async def on_ready(self):
        logger.info(f"[RaiseBot/on_ready] Bot is ready")
        channel = self.get_channel(self.config.bot_chat)
        await channel.send("I'm ready!")
        await self.tree.sync()  # Sync all app commands with Discord

    async def on_application_command_error(self, interaction: discord.Interaction,
                                           error: discord.app_commands.AppCommandError):
        logger.error('[RaiseBot/on_application_command_error] Ignoring exception in command tree', exc_info=error)

    async def on_error(self, event, *args, **kwargs):
        logger.exception(f'[RaiseBot/on_error] Ignoring exception in {event}')
        error_message = f"{traceback.format_exc()}"
        logger.error(f"[RaiseBot/on_error] {error_message}")
