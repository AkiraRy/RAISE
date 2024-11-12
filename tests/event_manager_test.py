from core import PubSub
from utils import Message, TelegramMessage, TextMessage
import asyncio


class Communication:
    def __init__(self, pubsub: PubSub):
        self.pubsub = pubsub
        self.pubsub.subscribe("back_response", self.send_to_brain)

    async def user_input(self, message: Message) -> None:
        """Simulate user input and publish to PubSub."""
        self.pubsub.publish("input", message)

    async def send_to_brain(self, message: Message) -> None:
        """Simulate sending a response back from the brain."""
        print(f"Communication received response: {message}")


class Brain:
    def __init__(self, pubsub: PubSub):
        self.pubsub = pubsub
        self.pubsub.subscribe("input", self.process_message)

    async def process_message(self, message: Message) -> None:
        """Process incoming message and generate a response."""
        print(f"Brain processing message: {message}")
        await self.generate_llm_response(message)

    async def generate_llm_response(self, message: Message) -> None:
        """Simulate LLM response generation."""
        # await asyncio.sleep(0.5)
        response = f"LLM Response to: {message.text_message.content}"
        print(f"Generated response: {response}")  # Add this print statement

        await self.send_to_communication(response)

    async def send_to_communication(self, response: str) -> None:
        """Send the generated response back to Communication."""
        # Use the Communication instance to handle the response
        text_msg = TextMessage(response)
        msg = Message(-1, text_message=text_msg)
        print(f'send {msg}')
        self.pubsub.publish('back_response', msg)


async def main():
    pubsub = PubSub(pooling_delay=0.1)

    # Create the Communication and Brain instances
    communication = Communication(pubsub)
    brain = Brain(pubsub)

    pubsub.start()
    # Start the PubSub system

    msg = Message(id=1, text_message=TextMessage('Hello, Brain!'))
    msg2 = Message(id=1, text_message=TextMessage('Hello, Brain!2'))
    # Simulate user input
    await communication.user_input(msg)
    pubsub.unsubscribe("back_response", communication.send_to_brain)
    await communication.user_input(msg2)

    await asyncio.sleep(0.5)

if __name__ == '__main__':
    asyncio.run(main())
