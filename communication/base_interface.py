import threading
from abc import ABC, abstractmethod


class BaseInterface(ABC):
    def __init__(self, pubsub: 'PubSub'):
        self.pubsub = pubsub

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def initialize(self):
        pass

    def start_in_thread(self) -> threading.Thread:
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        return thread

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def manage_event_loop(self):
        pass

