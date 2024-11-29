import asyncio
import datetime

import discord
from discord.ext import commands, tasks
from utils import TextMessage, DiscordMessage
from .. import logger


class MessageCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.ms_task_started = False
        self.bot = bot
        self.message = None
        self.lock = asyncio.Lock()

    async def cog_load(self) -> None:
        # as in receive response form pubsub, then send this message to discord
        self.bot.pubsub.subscribe(self.bot.subscribe_to, self.save_message)

    def cog_unload(self):
        if not self.ms_task_started:
            return
        self.ms.cancel()

    async def save_message(self, message):
        async with self.lock:
            self.message = message
            logger.info(f"[MessageCog/save_message] Saved {message} to the context")

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.ms_task_started:
            logger.info("[MessageCog/on_ready] Starting periodic message loop.")
            await asyncio.sleep(5)
            self.ms.start()
            self.ms_task_started = True

    @tasks.loop(seconds=1)
    async def ms(self):
        try:
            async with self.lock:
                if not self.message:
                    return

                id_channel = self.bot.config.bot_chat
                channel = self.bot.get_channel(id_channel)

                if not channel:
                    logger.error(f"[MessageCog/ms] Channel with ID {id_channel} not found.")
                    return

                logger.debug(f"[MessageCog/ms] Sending periodic message to channel {channel.name} (ID: {id_channel})")
                async with asyncio.timeout(5):
                    await channel.send(self.message.response_message)
                    self.message = None
        except discord.Forbidden:
            logger.error("[MessageCog/ms] Bot lacks permission to send messages.")
        except discord.HTTPException as e:
            logger.error(f"[MessageCog/ms] HTTP Exception while sending message: {e}")
        except asyncio.TimeoutError:
            logger.error("[MessageCog/ms] Timeout while sending message.")

    @commands.Cog.listener(name="on_message")
    async def handle_message(self, message: discord.Message) -> None:
        if message.author.id == self.bot.user.id:
            return
        if message.author.id != self.bot.config.creator_id:
            return

        sender_id = message.author.id
        msg_content = message.content
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
        logger.info(f"[MessageCog/handle_message] Sending processed message class to pubsub.")
        self.bot.pubsub.publish(self.bot.publish_to, msg_cls)
        await message.channel.typing()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MessageCog(bot))
