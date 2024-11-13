from typing import Optional, List
from . import logger, PROFILES_DIR
from ..memory import MemoryChain, Async_DB_Interface
from .model_handler import Model
from utils import Message


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Brain(metaclass=Singleton):
    def __init__(self, memory_manager: 'Async_DB_Interface',
                 model: Model,
                 persona_path: str,
                 user_name: str,
                 assistant_name: str,
                 pubsub: 'PubSub',
                 subscribe_to: str,
                 publish_to: str,
                 token_limit: int = 2000
                 ):
        # memory_manager - db instance, persona - name of the file where persona is stored
        # Important classes
        self.memory_manager: 'Async_DB_Interface' = memory_manager
        self.model: Model = model
        self.pubsub: 'PubSub' = pubsub

        # Config
        self.persona: Optional[str] = None
        self.user_name: str = user_name
        self.assistant_name: str = assistant_name
        self.token_limit: int = token_limit
        self.receive_topic: str = subscribe_to
        self.publish_to_topic: str = publish_to
        self.is_loaded_model: bool = False

        # initialization
        self.memories: List[dict] = list()
        self.load_persona(persona_path)
        self.pubsub.subscribe(subscribe_to, self.process_message)

    async def process_message(self, message: Message):
        if not self.is_loaded_model:
            logger.warning(f"[Brain/process_message] model is not loaded")
            return # send here an message with error inside

        content = message.text_content.content
        logger.info(f'[Brain/process_message] Got message from {self.receive_topic}, content: {content}')

        self.memories.append({
            'role': 'user',
            'content': content
        })
        logger.info(f"[Brain/process_message] Generating an llm response")
        response_content, usage, generation_time = self.model.generate(self.memories)
        self.memories.append({
            'role': 'assistant',
            'content': response_content.content
        })
        logger.info(f"[Brain/process_message] Received response from llm in {generation_time}s")

        message.response_message = response_content.content
        self.pubsub.publish(self.publish_to_topic, message)

    def close(self):
        if not self.model:
            logger.warning("[Brain/load_model] no model to close connection for")
            return False
        self.model.llm.close()
        del self.model.llm
        self.model.llm = None
        logger.info("[Brain/load_model] Successfully closed connection for model.")

    def load_model(self):
        if not self.model.llm_settings:
            logger.error("[Brain/load_model] No settings in the model.")
            return False

        is_loaded = self.model.load_model()
        self.is_loaded_model = is_loaded
        return is_loaded

    def load_persona(self, persona_path) -> None:
        try:
            path = PROFILES_DIR / f"{persona_path}.txt"
            logger.info(f"[Brain/load_persona] Trying to load AI Persona from file at {path}")

            with open(path, 'r') as f:
                lines = f.readlines()

            self.persona = ''.join(lines)

            self.memories.append({
                'role': 'system',
                'content': self.persona
            })

        except IOError:
            logger.error(f"[Brain/load_persona] There was an error during handling the file {self.persona}")
        else:
            logger.debug(f"[Brain/load_persona] Successfully loaded AI persona")

    async def fulfill_prompt(self) -> Optional[List[dict]]:
        try:
            logger.info(f"[Brain/fulfill_prompt] Fetching chat memories")
            fetchedMemories: MemoryChain = await self.memory_manager.get_chat_memory()
        except Exception as e:
            logger.error('[Brain/fulfill_prompt] Brain was damaged, could not remember anything {e}')
            return

        for memory in fetchedMemories:
            self.memories.append({
                'role': 'user' if self.user_name == memory.from_name else 'assistant',
                'content': memory.message
            })

        curr_tokens_amount = self.forget()  # forgets last message in a chat history if necessary
        logger.info(f"[Brain/fulfill_prompt] Current total number of tokens is {curr_tokens_amount}")
        return self.memories

    def forget(self) -> int:
        """returns total number of tokens at the end"""
        logger.info(f"Brain/fulfill_prompt] Forgetting last message in the chat history")
        prompt = self.model.format_prompt(self.memories)
        curr_total_tokens = self.model.count_tokens(prompt)

        while curr_total_tokens > self.token_limit:
            self.memories.pop(1)
            prompt = self.model.format_prompt(self.memories)
            curr_total_tokens = self.model.count_tokens(prompt)
        return curr_total_tokens
