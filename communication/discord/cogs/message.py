import asyncio
import datetime

import discord
from discord.ext import commands, tasks
from utils import Message, TextMessage, DiscordMessage
from .. import logger

from discord.message import Message

class MessageCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.message = None
        self.lock = asyncio.Lock()

    async def cog_load(self) -> None:
        # as in receive response form pubsub, then send this message to discord
        self.bot.pubsub.subscribe(self.bot.subscribe_to, self.save_message)
        self.ms.start()

    def cog_unload(self):
        self.ms.cancel()

    async def save_message(self, message):
        async with self.lock:
            self.message = message
            logger.info(f"[MessageCog/save_message] Saved {message} to the context")

    @tasks.loop(seconds=1)
    async def ms(self):
        try:
            async with self.lock:
                if self.message is None:
                    return

                logger.info("[MessageCog/ms] Sending message to bot chat")
                await self.send_message(self.message)
                self.message = None
        except Exception as e:
            logger.error(f"[MessageCog/ms] Error in ms loop: {e}")

    async def send_message(self, message: DiscordMessage):
        try:
            logger.info(f"[MessageCog/send_message] inside THIS")
            content = message.response_message
            if not content:
                content = 'Something went wrong. No response was generated'
            logger.info(f"[MessageCog/send_message] {content}")
            # channel = self.bot.get_channel(self.bot.config.bot_chat)
            # logger.info(f"[MessageCog/send_message] after channel getter")
            await message.channel.send(content)
        except Exception as e:
            logger.error(f"[MessageCog/send_message] Unexpectedly got an error {e}")

    @commands.Cog.listener(name="on_message")
    async def handle_message(self, message: discord.Message) -> None:
        if message.author.id == self.bot.user.id:
            return
        if message.author.id != self.bot.config.creator_id:
            return

        sender_id = message.author.id
        msg_content = message.content
        nowtime = datetime.datetime.now()
        datetime_msg = datetime.datetime.now().astimezone()

        logger.debug(
            f"[MessageCog/handle_message] We got message from the user: {sender_id}, content: {msg_content}")

        msg_cls = DiscordMessage(
            id=message.id,
            from_user=self.bot.creator_username,
            datetime=datetime_msg,
            text_content=TextMessage(msg_content),
            channel=message.channel
        )
        logger.info(f"[MessageCog/handle_message] Sendi ng processed message class to pubsub.")
        self.bot.pubsub.publish(self.bot.publish_to, msg_cls)
        # await message.channel.typing()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MessageCog(bot))
