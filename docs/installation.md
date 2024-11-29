# Installation and Setup ⚙️

!!! Everything should be run from the root of this project


First step is always to either download zip and extract it or run
```
git clone https://github.com/AkiraRy/RAISE.git
```

Second step is to set up environment. If you don't want to use discord or telegram, then simply delete the line form environment.yaml that contains certain library
```
conda env create -f environment.yaml
```
After you've created an environment you should activate it

```
conda activate raise
```
Third step is to install llama-cpp-python and build it in the activated environment:\
CPU:
```
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```
GPU:\
First you need to set an env variable. Using either `set` or `export` depending on the os you use
```
CMAKE_ARGS="-DGGML_CUDA=on" 
```
Now you can run this to install and build llama-cpp-python with cuda support
supported cuda version are  12.1, 12.2, 12.3, 12.4 or 12.5
```
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/<cuda-version>
```
Where `<cuda-version>` is one of the following:
- cu121: CUDA 12.1
- cu122: CUDA 12.2
- cu123: CUDA 12.3
- cu124: CUDA 12.4
- cu125: CUDA 12.5

Forth step is to activate docker containers using
```commandline
docker-compose up -d
```

Now mostly everything is set up. We got 2 thing left to do. 

1. Config

For detailed information look in [docs](docs/configs.md)

You can create multiple configs in the `config/profiles`. All of them should follow default_settings.yaml structure
If you want to use custom profile, then you should change the `SETTINGS_FILE` variable in `config/settings.py` to your desired profile.

`llm_type` Should be named the same as your llm settings file name in the `config/llm_settings` dir\
In your llm settings:\
`llm_model_name`: should be a name of the repo on hf. example: `cjpais/llava-1.6-mistral-7b-gguf`\
`llm_model_file`: mode file name you're going to use from that repo. example : `llava-v1.6-mistral-7b.Q3_K_XS.gguf`

(Currently only telegram interface is supported.)
You need to specify each setting in the `telegram` section
Here is [link](<https://www.directual.com/lesson-library/how-to-create-a-telegram-bot>) which will help you set up your own bot in the telegram.

If you haven't edited docker-compose file, then most settings in the weaviate can be left as they are. 
You only need to specify `author_name` and `class_name` 

2. environment variables 

In the `.env.simple` you should specify your bot's api token and Hugging face token to download model.
After that you should rename it to `.env`

!! If you wish to use your custom config, then you should change `config_name` in the .env Example: `settings` (no file extension)

3. Weaviate collection setup

If you set up everything correctly in your settings, then you should be able to run setup.
Which will initialize collection in weaviate db and download llm model.
```commandline
python -m setup
```

Now everything should be ready to start.

[go back to README](../README.md)
