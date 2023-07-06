import os
from weaviate import  Client, WeaviateStartUpError, exceptions
from transformers import  AutoTokenizer
from pathlib import Path
from dotenv import load_dotenv
tokenizer_dir = Path(__file__).resolve().parent / 'tokenizer_files'
TOKENIZER = AutoTokenizer.from_pretrained(str(tokenizer_dir))

load_dotenv()

MAIN_FOLDER_PATH = Path(os.getenv('MAIN_FOLDER_PATH'))


class Kurisu:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, memory, token_limit=1600):
        if not self._initialized:
            self._initialized = True
            assert isinstance(memory, list) and all(
                isinstance(item, dict) for item in memory), "'memory' parameter must be a list of dictionaries."

            self.class_name: str = os.getenv('CLASS_NAME')
            self.memory: list[dict] = memory
            self.token_limit: int = token_limit
            self.history = MAIN_FOLDER_PATH / 'history.txt'
            self.persona: str = ''
            self.load_history()
            self.connectDB()

    def connectDB(self):
        """
            connection to database
        """
        try:
            self.client = Client(os.getenv('CLIENT_URL'))
            print('Connected Memory Module')
        except exceptions.AuthenticationFailedException as e:
            raise WeaviateStartUpError('Failed to connect to Weaviate server: {}'.format(str(e)))

    def forget(self):
        """
            I will add this just in case it exceeds the limit
        """
        curr_total_tokens = self.count_tokens()

        while curr_total_tokens > self.token_limit:
            self.memory.pop(0)
            curr_total_tokens = self.count_tokens()

    async def memory_context(self, concept):
        max_distance = 0.20
        where_filter = {
            "path": ["from"],
            "operator": "Equal",
            "valueText": "Akira",
        }
        response = (
            self.client.query
            .get("MemoryK", ["from", "message"])
            .with_near_text({
                "concepts": [concept],
                'distance': max_distance
            })
            .with_where(where_filter)
            .with_limit(2)
            .with_additional(["distance"])
            .do()
        )
        return response['data']['Get']['MemoryK']

    async def fulfilingPrompt(self):
        """
            fetch from vectorDB
        """
        prompt = self.persona
        prompt += '\n\nKurisu may use the context below to answer any question if it is related\n\n<|CONTEXT|>'
        prompt+= '\n\nToday`s date is the <|DATETIME|>'
        prompt+= '\n    -- Transcript --\n'

        fetchedMemories = await self.Remember()
        fetchedMemories.reverse()
        for memories in fetchedMemories:
            self.memory.append(memories)
            prompt+=f"{memories['from']}: {memories['message']}\n"
        prompt+="""### Akira: <input>\n### Kurisu:"""

        if self.count_tokens() > self.token_limit:
            self.forget()
        return prompt

    async def Remember(self, max_shards: int = 20) -> list[dict]:
        content = {
            'path': ['datetime'],
            'order': 'desc'
        }
        try:
            return  (
                self.client.query
                .get("MemoryK", ["from", 'message'])
                .with_sort(content)
                .with_limit(max_shards)
                .do()
            )['data']['Get'][self.class_name]
        except exceptions.UnexpectedStatusCodeException:
            print('Kurisu was unable to remember')

    async def add_memories(self, memories: list[dict]):
        """
            name: USERNAME
            message: actual context
            datetime: time when it was added

            maybe do it here (addition to database)
        """
        if len(memories) != 2:
            raise Exception('to much/not enough memory')
        required_properties = ["name", "message", "datetime"]

        # Check if all dictionaries have the required properties
        if  not all(all(prop in memory for prop in required_properties) for memory in memories):
            raise Exception('In one/both of dictionaries missing argument')

        for shard in memories:

            obj = (
                {
                    "from": shard['name'],
                    "message": shard['message'],
                    "datetime": shard['datetime']
                }
            )

            if self.client is not None:
                try:
                    response = self.client.data_object.create(obj, class_name=self.class_name)
                except exceptions.ObjectAlreadyExistsException:
                    print('This is already in memory')
                except :
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
            total_tokens+=len(TOKENIZER.tokenize(self.persona))

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
