import logging
import os
import time
import weaviate
from weaviate import Client, WeaviateStartUpError, exceptions
from transformers import AutoTokenizer
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

tokenizer_dir = Path(__file__).resolve().parent / 'tokenizer_files'
TOKENIZER = AutoTokenizer.from_pretrained(str(tokenizer_dir))
CREATOR_USERNAME = os.getenv('CREATOR_USERNAME')
MAIN_FOLDER_PATH = Path.cwd().parent.absolute()


class Kurisu:
    _instance = None
    _initialized = False

    def nullify(self):
        self._instance = None
        self._initialized = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def bind(self, function):
        # IN PRODUCTION
        self.func = function

    def __init__(self, memory=None, token_limit=1600):

        if self._initialized:
            return
        self._initialized = True
        if memory is None:
            memory = [{}]
        assert isinstance(memory, list) and all(
            isinstance(item, dict) for item in memory), "'memory' parameter must be a list of dictionaries."

        self.class_name: str = os.getenv('CLASS_NAME')
        self.memory: list[dict] = memory
        self.token_limit: int = token_limit
        self.history = MAIN_FOLDER_PATH / 'history.txt'
        self.persona: str = ''
        self.func = None
        self.client = None
        self.load_history()  # Blueprint for prompt
        self.connect_db()

    def connect_db(self):
        """
            connection to database
        """
        max_retries = 10
        retry_delay = 2  # Delay in seconds between retries

        for retry in range(max_retries):
            try:
                self.client = Client(os.getenv('CLIENT_URL'))
                print('Connected Memory Module')
                return  # Connection successful, exit the loop
            except weaviate.exceptions.AuthenticationFailedException as e:
                print('Failed to connect to Weaviate server:', str(e))
                # Handle authentication failure, if needed
            except weaviate.exceptions.WeaviateStartUpError as e:
                print('Failed to connect to Weaviate server:', str(e))
                # Handle connection error, if needed

            print('Retrying connection in', retry_delay, 'seconds...')
            time.sleep(retry_delay)

        # Connection unsuccessful after max_retries
        raise WeaviateStartUpError('Failed to connect to Weaviate server after multiple attempts')

    def forget(self):
        """
            Clears memories in case it exceeded token_limit
        """
        curr_total_tokens = self.count_tokens()

        while curr_total_tokens > self.token_limit:
            self.memory.pop(0)
            curr_total_tokens = self.count_tokens()

    async def memory_context(self, concept):
        """
            Fetches context from client
        """
        if self.client is None:
            return

        max_distance = 0.50
        where_filter = {
            "path": ["from"],
            "operator": "Equal",
            "valueText": CREATOR_USERNAME,
        }

        try:
            return (
                self.client.query
                .get(self.class_name, ["from", "message"])
                .with_near_text({
                    "concepts": [concept],
                    'distance': max_distance
                })
                .with_where(where_filter)
                .with_limit(2)
                .with_additional(["distance"])
                .do()
            )['data']['Get'][self.class_name]
        except exceptions:
            return None

    async def fulfilling_prompt(self) -> list:
        """
            fetch from vectorDB
        """
        # prompt = self.persona # return as character context maybe not use it here?
        prompt = []
        try:
            fetchedMemories = await self.remember()  # chat history
        except exceptions:
            print('Brain was damaged, could not remember anything')
            return

        fetchedMemories.reverse()  # chat order

        for memories in fetchedMemories:
            self.memory.append(memories)

            if memories['from'] == CREATOR_USERNAME:
                prompt.append({"role": "user", "content": memories['message'].strip()})
            else :
                prompt.append({"role": "assistant", "content": memories['message'].strip()})

        # empty space for user input
        prompt.append({"role": "user", "content": ''})

            # prompt += f"{memories['from']}: {memories['message'].strip()}\n"
        # prompt += f"""{CREATOR_USERNAME}: <input>
# ASSISTANT: Kurisu:"""

        if self.count_tokens() > self.token_limit:
            self.forget()

        logging.info(f"current number of tokens is {self.count_tokens()}")
        return prompt

    async def remember(self, max_shards: int = 20):
        """
            return 20(default) messages from both user and ai
        """
        if self.client is None:
            return None

        content = {
            'path': ['datetime'],
            'order': 'desc'
        }
        try:
            return (
                self.client.query
                .get(self.class_name, ["from", 'message', 'datetime'])
                .with_sort(content)
                .with_additional(['id'])
                .with_limit(max_shards)
                .do()
            )['data']['Get'][self.class_name]
        except exceptions.UnexpectedStatusCodeException:
            print('Kurisu was unable to remember')

    async def add_memories(self, memory: dict):
        """
            name: USERNAME
            message: actual context
            datetime: time when it was added

            maybe do it here (addition to database)
        """
        if self.client is None:
            return

        required_properties = ["name", "message", "datetime"]

        # Check if all dictionaries have the required properties
        if not all(prop in memory for prop in required_properties):
            raise Exception('In one/both of dictionaries missing argument')

        obj = (
            {
                "from": memory['name'],
                "message": memory['message'],
                "datetime": memory['datetime']
            }
        )

        try:
            response = self.client.data_object.create(obj, class_name=self.class_name)
        except exceptions.ObjectAlreadyExistsException:
            print(f'This is already in memory\n{obj}\n')
        except weaviate.SchemaValidationException:
            raise exceptions.SchemaValidationException
        else:
            print(f'Successfully added to memory, uuid: {response}')

    def count_tokens(self):
        total_tokens = 0
        for dictionary in self.memory:
            for key, value in dictionary.items():
                key_tokens = len(TOKENIZER.tokenize(str(key)))
                value_tokens = len(TOKENIZER.tokenize(str(value)))
                total_tokens += key_tokens + value_tokens

        if self.persona is not None:
            total_tokens += len(TOKENIZER.tokenize(self.persona))

        return total_tokens

    def load_history(self):
        try:
            with open(self.history, 'r') as f:
                lines = f.readlines()

            self.persona = ''.join(lines)
        except IOError:
            print(f"There was an error during handling the file {self.history}")
        else:
            print("History Module Loaded Successfully!")