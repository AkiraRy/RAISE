import datetime
import io

import discord
from discord.ext import commands
from utils import Message_server
from .. import logger


class MessageCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("[MessageCog/on_ready] Message cog is loaded.")

    async def _get_response(self, mssg_id, creator_name, datetime_msg, message_from_user):
        message_srv = Message_server(
            id=mssg_id,
            from_user=creator_name,
            datetime=datetime_msg,
            text_content=message_from_user
        )

        logger.info(f"[MessageCog/_get_response] Sending message to brain handler")
        return await self.bot.brain_helper.generate_response(message_srv)

    async def _handle_text_message(self, message: discord.Message) -> None:
        sender_id = message.author.id
        msg_content = message.content
        datetime_msg = datetime.datetime.now().astimezone()

        logger.debug(
            f"[MessageCog/handle_message] Got message from the user: {sender_id}, content: {msg_content}")

        logger.info(f"[MessageCog/handle_message] Sending message to brain handler")
        await message.channel.typing()
        response = await self._get_response(mssg_id=message.id, creator_name=self.bot.creator_username, datetime_msg=datetime_msg, message_from_user=msg_content)

        if response is None:  # add debug here
            await message.channel.send(f"No Generated Response")
            return

        await message.channel.send(response)

        if not self.bot.config.generate_voice:
            # possible debug msg?
            return

        await self._send_voice(message, response)

    async def _send_voice(self, message: discord.Message, text: str):
        """
        :param message: discord message, to access channel and being able to send an information there
        :param text: what needs to be generated in tts
        :return: None
        """
        # make it create a message with -# saying generating voice
        # after that delete that message
        msg = await message.channel.send(content=f"-# generating voice。。。", )
        voice_bytes = await self.bot.plugin_manager.tts(text)
        voice_buffer = io.BytesIO(voice_bytes)
        voice_buffer.seek(0)
        await message.channel.send(file=discord.File(voice_buffer, filename="voice.ogg"))
        await msg.delete()

    async def _handle_message_with_files(self, message: discord.Message) -> None:
        pass

    @commands.Cog.listener(name="on_message")  # this is also for file :despair:
    async def handle_message(self, message: discord.Message) -> None:
        if message.author.id == self.bot.user.id:
            return
        if message.author.id != self.bot.config.creator_id:
            return

        if message.attachments:  # If the message has attachments
            return await self._handle_message_with_files(message)

        return await self._handle_text_message(message)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MessageCog(bot))
