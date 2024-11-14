import datetime
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
                 use_memories: bool,
                 save_memories: bool,
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
        self.use_memories: bool = use_memories
        self.save_memories = save_memories
        self.is_loaded_model: bool = False

        # initialization
        self.memories: List[dict] = list()
        self.load_persona(persona_path)
        self.pubsub.subscribe(subscribe_to, self.process_message)

    async def start(self):
        self.load_model()
        if self.use_memories:
            logger.info(f"[Brain/start] initializing chat data/memories")
            await self.initialize_memories()
            return
        logger.info(f"[Brain/start] Not using chat data/memories")

    async def process_message(self, message: Message):
        if not self.is_loaded_model:
            logger.warning(f"[Brain/process_message] Model({self.model.llm_settings.llm_model_name}) is not loaded")
            message.response_message = f'Model({self.model.llm_settings.llm_model_name}) is not loaded.'
            self.pubsub.publish(self.publish_to_topic, message)
            return  # send here an message with error inside

        # 1. Getting current memories with user input
        content = message.text_content.content
        logger.info(f'[Brain/process_message] Got message from {self.receive_topic}, content: {content}')

        self.memories.append({
            'role': 'user',
            'content': content
        })
        # 1.1 checking if we use more tokens than allowed in prompt
        self.forget()

        # 2. Response generation
        logger.info(f"[Brain/process_message] Generating an llm response")
        response_content, usage, generation_time = self.model.generate(self.memories)

        self.memories.append({
            'role': 'assistant',
            'content': response_content.content
        })

        # saving to memory (optional)
        logger.info(f"[Brain/process_message] Received response from llm in {generation_time}s")

        if self.save_memories:
            logger.info("[Brain/process_message] saving memories.")
            mem_chain = MemoryChain()
            mem_chain.add_object(
                from_name=message.from_user,
                message=content,
                time=message.datetime  # DO SOMETHING?
            )
            mem_chain.add_object(
                from_name=self.assistant_name,
                message=response_content.content,
                time=datetime.datetime.now()
            )
            await self.memory_manager.add_memories(memory_chain=mem_chain)

        if not self.use_memories:
            logger.info(f"[Brain/process_message] clearing chat info from context")
            self.memories = self.memories[:1]  # we only leave our persona

        message.response_message = response_content.content
        self.pubsub.publish(self.publish_to_topic, message)

    def close(self):
        if not self.model:
            logger.warning("[Brain/close] no model to close connection for")
            return False
        self.model.llm.close()
        del self.model.llm
        self.model.llm = None
        logger.info("[Brain/close] Successfully closed connection for model.")

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
            logger.info(f"[Brain/load_persona] Successfully loaded AI persona")

    async def initialize_memories(self) -> None:
        try:
            logger.info(f"[Brain/initialize_memories] Fetching chat memories")
            fetchedMemories: MemoryChain = await self.memory_manager.get_chat_memory()
        except Exception as e:
            logger.error(f'[Brain/initialize_memories] Brain was damaged, could not remember anything {e}')
            return

        if not fetchedMemories:
            logger.warning(f"[Brain/initialize_memories] Couldn't initialize memories. None were retrieved.")

        for memory in fetchedMemories.memories:
            self.memories.append({
                'role': 'user' if self.user_name == memory.from_name else 'assistant',
                'content': memory.message
            })

        curr_tokens_amount = self.forget()  # forgets last message in a chat history if necessary
        logger.info(f"[Brain/initialize_memories] Current total number of tokens is {curr_tokens_amount}")
        logger.info(f"[Brain/initialize_memories] Successfully initialized memories.")

    def forget(self) -> int:
        """returns total number of tokens at the end"""
        prompt = self.model.format_prompt(self.memories)
        curr_total_tokens = self.model.count_tokens(prompt)

        while curr_total_tokens > self.token_limit:
            logger.info(
                f"Brain/forget] Forgetting last message in the chat history. Current lengths of memories {len(self.memories)}")
            self.memories.pop(1)
            prompt = self.model.format_prompt(self.memories)
            curr_total_tokens = self.model.count_tokens(prompt)
        return curr_total_tokens


