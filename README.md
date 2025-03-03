# RAISE 🔥

Have you ever dreamed of having someone with whom you can speak whenever you like?
RAISE aims to help you with this. What is even better everything is entirely locally hosted.
Using telegram/discord as a chatting interface, whisper for transcribing your voice messages and voicevox for voice generation. 
We also have a Weaviate vectordb to store your chat history data. 
Whenever you ask for something we first use similarity search on stored documents to retrieve relevant parts.
After that we prompt an LLM with all the info, giving you more relevant answers.
In the future, I plan to make a classifier, using which LLM will classify user query for certain tasks.
Based on those tasks LLM will be able to do a lot of things. Like searching web, telling current weather conditions, calendar appointments and much more!

# Out of the box features
at v1.0
1. Telegram, discord interfaces for messaging with your ai assistant
2. Vector db for memory management.
3. Personality of your ai assistant.
4. Full customization via config files.
5. Ability to run different modules on different machines. 
    - You can runllm inference on one machine, telegram/discord interference on another. Everything works on restapi servers

# Prerequisites ⚠️
I'll add from my self a little bit. 
If you want to everything work from the get go, then install nvidia cuda toolkit in the default installation directory. Same with MSVC compiler.\
I've tried to make it work with custom installation dir and failed miserably, spending 24h. If you don't wish to waste time like me, simply install where it wants (windows)\
(I highly advise against installing cudatoolkit in conda env, At the very least I couldn't make it work.)

1. Follow instructions for prerequisites in the [llama-cpp-python](<https://github.com/abetlen/llama-cpp-python?tab=readme-ov-file>) repo
2. conda for package managing
3. docker.  weaviate and whisper are hosted in a docker container
4. git (optional)
5. at least 6GB VRAM and/or 16GB of RAM

Whisper small model will take around 2gb of vram, you can choose even smaller model in the docker compose or make it run on cpu instead.
If you have 6gb of vram like me, you should change number of gpu layers in the model config, so that some of them will be offloaded to RAM.

16GB of RAM will be an only viable option if you run docker container and python script, Everything else should be disabled.
32GB of RAM lets me run other apps alongside

# Installation and Setup ⚙️

How to install and set up everything can be found [here](docs/installation.md)

# Running:
Make sure that your conda env is activated and that you're in the root of the project.
```commandline
python -m main
```

# Project RoadMap
Here I will write my current progress and what I want to implement in the future.

## Completed:
- LLM interference
- Vector db memory
- Telegram/Discord integration
- Config customization
- AI personality
- Decoupled structure. Memory, LLM interference, communication modules run in their own servers/scripts

## Plans for the future

1. Classifier for user queries to enable llm use different module. Like web search, weather forecast and so on 
2. Backend that will load plugins and add routes dynamically. For things like whisper, rvc, voicevox.
3. A gui app that will support streaming from the mode. Also using gui you won't need to use discord/telegram
4. Ability to save document information and retrieve relevant part to user query. (RAG)
5. 

### Plugins
| Plugin             | Status |
|--------------------|--------|
| RVC STS            | 🔴     |

# Acknowledgement

This project wouldn't have been possible without these libraries and people that built them:

1. [llama-cpp-python](<https://github.com/abetlen/llama-cpp-python>) model interference
2. [weaviate](<https://github.com/weaviate/weaviate>) vector database
3. [python-telegram-bot](<https://github.com/python-telegram-bot/python-telegram-bot>) telegram bot interface
4. [whisper](<https://github.com/openai/whisper>) STT model 
5. [voicevox](<https://github.com/VOICEVOX>) TTS model

If I forgot to include your library or your work here, please open an issue.

# Contribution

For any inquiries or issues, please open an issue on the repository or contact me [AkiraRy](https://github.com/AkiraRy).

# License
 
If you use this software, please credit me via GitHub [link](https://github.com/AkiraRy).\
This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.
