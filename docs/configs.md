# Here I will try to explain what each setting do in the default config

* `llm_type: llava`          str This variable specifies which model settings profile to use
* 'brain':
    - `add_context: true`       bool On each message you send to your AI assistant it will try to fetch similar message for the additional context.
    - `assistant_name: # Raise`                           str This is how you want to call your assistant
    - `creator_name: # Should be your accounts name, not @` str Your name
    - `persona_path: default_persona` str This is the name of your AI persona file located at `assets/persona_description`
    - `use_memories: true`      bool Whether to fetch last 20(default) messages from db when you start your client fresh. Also, if to include current messages in the chat to history
    - `save_memories: true`     bool If you want to save your messages to the vector db.
* `pubsub:`                      Here is config for Publish subscribe system. Should be left as it is. Unless you know what you're doing.
   - `input_message_topic: message_received`         str Name of the topic to which communication module publishes message from the user. Later preprocessed by the brain.
   - `processed_message_topic: message_preprocessed` str Name of the topic to which brain publishes response from an AI. Later sent to the user using communication module.
* `telegram:`                    Here is config for telegram communication module. In future if you don't want to use telegram, but discord or gui instead. Simply delete this part.
   - `creator_id: # str, for filtering messages`               str By default bots on telegram are publicly available. Meaning anyone can access your bot. You can get this id simply by putting some random numbers her. Then trying to message something to your bot and grab the id from the console logs 
* 'discord':
   - `creator_id: # str, for filtering messages`               str By default bots on telegram are publicly available. Meaning anyone can access your bot. You can get this id simply by putting some random numbers her. Then trying to message something to your bot and grab the id from the console logs 
   - 'bot_chat' # int simply right-click on a message channel and copy its id. Assistant will use it to communicate with you
* `weaviate:`
   - `alpha: 0.5`                                                               str This variable is used in the hybrid similarity search. Higher values will prioritise more vector search while lower values will prioritise more keyword search.
   - `author_name: # str your name under which this program will save memories` str This should be the same as creator_username in telegram module. Used this to store user instance in the vector db and also search based on this variable.
   - `class_name: # str class name under which we will collect your memories`   str This is where your memories will be saved. You can name your collection as `memory1`, If you want to try out new persona or different model you can create new collection, but make sure it has different name. If you want new collection use `python -m setup` and make sure to comment out the line for model download
   - `grpc_host: localhost # everything else can stay as default`               str Self explanatory. This is where you can access grpc. gRPC's usage will be implemented in the future. TL;DR gRPC is faster than using REST+GraphQL
   - `grpc_port: 50051`                                                         int Self explanatory. Same as above
   - `grpc_secure: false`                                                      bool Whether to use ssl.
   - `http_host: localhost`                                                     str Same as gRPC but for REST implementation
   - `http_port: 8080`                                                          int
   - `http_secure: false`                                                      bool
   - `limit: 2`                                                                 int Number of similar messages to retrieve when using similarity search on a user query.
   - `max_distance: 0.6`                                                      float This number specifies how far can those messages be from the user query.
   - `max_retries: 5`                                                          int Number of times weaviate module will try to connect to weaviate db
   - `retry_delay: 5`                                                          int How much time passes between each retry for connection
   - `sim_search_type: hybrid`                                                 str Can be either one of those: bm_25 (keyword search ) near_text (vector similarity search) hybrid (mix of previous two)

# Here is example config for llava model I'm using. 
Yours won't differ that much so use it as template.

* `chat_format: mistral-instruct`                      str
* `cuda: 1`                                            int This variable indicates whether to use gpu acceleration. If set to 0, but n_gpu_layers are > 0 will log a working and set it manually to 0
* `endpoint: null`                                     str Use this endpoint if you don't want your model to be locally hosted. Currently, there is no support for this. Implementation in the future.
* `llm_model_file: llava-v1.6-mistral-7b.Q3_K_XS.gguf` str Exact name of the model file you want to use in the `llm_model_name` repo on hf. Current only HF model and download support. If you want to help me implement other methods feel free to do so. 
* `llm_model_name: cjpais/llava-1.6-mistral-7b-gguf`   str name of the repo on HF
* `local: true`                                       bool This is whether to use local inference or not. If set to true, will raise an error if endpoint isn't null
* `max_tokens: 1024`                                   int Max number of tokens a model can generate in a single response. 
* `min_p: 0.05`                                      float The min-p value to use for minimum p sampling. Minimum P sampling as described in https://github.com/ggerganov/llama.cpp/pull/3841
* `n_batch: 256`                                       int Prompt processing maximum batch size
* `n_ctx: 8192`                                        int Text context, 0 = from model. In simple terms this is a maximum number of tokens can exist in a single prompt.
* `n_gpu_layers: -1`                                   int Number of layers to offload to GPU. If -1, all layers are offloaded.
* `repeat_penalty: 1.18`                             float The penalty to apply to repeated tokens.
* `seed: null`                                         int The seed to use for sampling
* `stop:`                                        list[str] A list of strings to stop generation when encountered.
    - 'Q:'
    - \n
* `stream: false`                                     bool Whether to stream tokens. Currently, setting this to true will most likely break everything. It will be implemented in future for gui communication module only.
* `temperature: 0.5`                                 float This number specify how random response should be
* `top_k: 50`                                          int The top-k value to use for sampling. Top-K sampling described in academic paper "The Curious Case of Neural Text Degeneration" https://arxiv.org/abs/1904.09751
* `top_p: 1.0`                                       float The top-p value to use for nucleus sampling. Nucleus sampling described in academic paper "The Curious Case of Neural Text Degeneration" https://arxiv.org/abs/1904.09751
* `typical_p: 1.0`                                   float The typical-p value to use for sampling. Locally Typical Sampling implementation described in the paper https://arxiv.org/abs/2202.00666.
* `verbose: false`                                    bool Prints very detailed information to the console. Like model metadata. Metadata when generating like how much time it took to generate response

