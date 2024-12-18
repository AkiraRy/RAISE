import asyncio
import threading
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any, Coroutine, Type
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
        self.stop_event = asyncio.Event()

    def start(self):
        logger.info(f"[PubSub/start] Starting worker thread")
        """Start the PubSub event loop in a separate thread."""
        self._thread = threading.Thread(target=self._start_loop, daemon=True)
        self._thread.start()

    def _start_loop(self):
        logger.info(f"[PubSub/_start_loop] Starting worker loop")
        """Set up the event loop to run in the thread."""
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.start_working())
        except RuntimeError:
            logger.info("[PubSub/_start_loop] Event loop stopped before Future completed.")
        finally:
            self.loop.close()
            logger.info("[PubSub/_start_loop] Worker loop stopped and event loop closed")

    async def start_working(self) -> None:
        """Continuously check and process messages from topics."""
        logger.info("[PubSub/start_working] Entering main working loop")
        try:
            while not self.stop_event.is_set():  # Async check with asyncio.Event
                for topic, topic_data in self.channels.items():
                    if not topic_data.queue.empty():
                        message = await topic_data.queue.get()
                        listeners = topic_data.listeners
                        await self._propagate_to_listeners(listeners, message)
                        topic_data.queue.task_done()
                await asyncio.sleep(self.pooling_delay)
        except asyncio.CancelledError:
            logger.error("[PubSub/start_working] Loop cancelled during shutdown")
        except RuntimeError:
            logger.error("[PubSub/start_working] Event loop stopped before Future completed.")
        finally:
            logger.info("[PubSub/start_working] Exiting main working loop")

    async def _shutdown(self):
        self.stop_event.set()
        # tasks = [t for t in asyncio.all_tasks(self.loop) if not t.done()]
        # for task in tasks:
        #     task.cancel()
        # try:
        #     await asyncio.gather(*tasks, return_exceptions=True)
        # except Exception as e:
        #     logger.warning(f"[PubSub/_shutdown] Exception during shutdown: {e}")

    def stop(self):
        logger.info(f"[PubSub/stop] Stopping PubSub system")
        future = asyncio.run_coroutine_threadsafe(self._shutdown(), self.loop)  # Stop async tasks
        future.result()
        logger.info(f"[PubSub/stop] Stopping PubSub loop")
        self.loop.call_soon_threadsafe(self.loop.stop)
        if self._thread:
            logger.info(f"[PubSub/stop] Stopping PubSub thread")
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
            # await listener(message)
            if asyncio.iscoroutinefunction(listener):
                asyncio.create_task(listener(message))
            else:
                logger.warning(f"[PubSub/_propagate_to_listeners] Listener is not a coroutine: {listener}")
                listener(message)

    def unsubscribe(self, topic: str, handler: Callable[[Any], Coroutine]) -> None:
        """Unsubscribe a handler from a given topic."""
        if topic in self.channels:
            self.channels[topic].listeners = [h for h in self.channels[topic].listeners if h != handler]

            if not self.channels[topic].listeners:  # Remove topic if no subscribers remain
                del self.channels[topic]
                logger.info(f"[PubSub/unsubscribe] Topic '{topic}' removed due to no listeners")
