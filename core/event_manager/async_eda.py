import asyncio
import threading
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any, Coroutine, Type, Optional
from utils import Message
from config import logger

@dataclass
class Topic:
    queue: asyncio.Queue = None
    listeners: List[Callable[[Any], Coroutine]] = field(default_factory=list)


class PubSub:
    def __init__(self, message_type: Type[Message] = Message, pooling_delay: float = 0.5):
        self.channels: Dict[str, Topic] = {}
        self.message_type = message_type
        self.pooling_delay = pooling_delay
        self.loop = asyncio.new_event_loop()
        self._thread = None

    def start(self):
        logger.info(f"[PubSub/start] Starting worker thread")
        """Start the PubSub event loop in a separate thread."""
        self._thread = threading.Thread(target=self._start_loop, daemon=True)
        self._thread.start()

    def _start_loop(self):
        logger.info(f"[PubSub/_start_loop] Starting worker loop")
        """Set up the event loop to run in the thread."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.start_working())

    async def start_working(self) -> None:
        """Continuously check and process messages from topics."""
        while True:
            for topic, topic_data in self.channels.items():
                if not topic_data.queue.empty():
                    message = await topic_data.queue.get()
                    listeners = topic_data.listeners
                    await self._propagate_to_listeners(listeners, message)
                    topic_data.queue.task_done()
            await asyncio.sleep(self.pooling_delay)

    def stop(self):
        logger.info(f"[PubSub/stop] Stopping PubSub system")
        """Stop the event loop in the background thread."""
        self.loop.call_soon_threadsafe(self.loop.stop)
        if self._thread:
            self._thread.join()

    def subscribe(self, topic: str, handler: Callable[[Any], Coroutine]) -> None:
        """Subscribe a handler to a given topic."""
        if topic not in self.channels:
            topic_cls = Topic(queue=asyncio.Queue())
            logger.info(f"[PubSub/subscribe] creating a new topic {topic}")
            self.channels[topic] = topic_cls
        logger.info(f"[PubSub/subscribe] subscribed to a {topic}")
        self.channels[topic].listeners.append(handler)

    def publish(self, topic: str, message: Message) -> None:
        """Publish a message in a thread-safe way."""
        if topic not in self.channels:
            logger.warning(f"[PubSub/publish] publishing to a topic no one listens to. Ignoring")
            return
        logger.info(f'[PubSub/publish] Publishing to a {topic} topic.')
        task = self.channels[topic].queue.put(message)
        asyncio.run_coroutine_threadsafe(task, self.loop)

    async def _propagate_to_listeners(self, listeners: List[Callable[[Any], Coroutine]], message: Message):
        """Send the message to all registered listeners for a topic."""
        for listener in listeners:
            asyncio.create_task(listener(message))

    def unsubscribe(self, topic: str, handler: Callable[[Any], Coroutine]) -> None:
        """Unsubscribe a handler from a given topic."""
        if topic in self.channels:
            self.channels[topic].listeners = [h for h in self.channels[topic].listeners if h != handler]

            if not self.channels[topic].listeners:  # Remove topic if no subscribers remain
                del self.channels[topic]
