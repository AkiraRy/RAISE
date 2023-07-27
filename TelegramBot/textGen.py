# import os
# hostname = "investigation-prostores-closer-framework.trycloudflare.com" #example
# response = os.system("ping -n 1 " + hostname)
#
# #and then check the response...
# if response == 0:
#   print(f"{hostname} is up!")
# else:
#   print(f"{hostname} is down!")
import json
import os
import time

import requests
from dotenv import load_dotenv
# For local streaming, the websockets are hosted without ssl - http://

def run(prompt):
    load_dotenv()
    HOST = os.getenv('HOST') # the cloudflare address
    URI = f'{HOST}/v1/generate'
    # print(URI)
    request = {
        'prompt': prompt,
        'max_new_tokens': 400,

        # Generation params. If 'preset' is set to different than 'None', the values
        # in presets/preset-name.yaml are used instead of the individual numbers.
        'preset': 'None',
        'do_sample': True,
        'temperature': 0.8,
        'top_p': 0.1,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.18,
        'repetition_penalty_range': 0,
        'top_k': 40,
        'min_length': 0,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,
        'stop_at_newline': False,
        'seed': -1,
        'add_bos_token': True,
        'truncation_length': 2300,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'stopping_strings': ["\n### Kurisu:", "\n### Akira:", "\nA", "\nK", "\nAkira:", "\n Akira: ", " AKira", " \nAkira"]
    }
    # start_time = time.time()
    response = requests.post(URI, json=request)
    # print(response.elapsed)


    # end_time = time.time()
    # execution_time = end_time - start_time

    if response.status_code == 200:
        result = response.json()['results'][0]['text']
        return result, response.elapsed.total_seconds()-0.79
    # 0.79


if __name__ == '__main__':

    prompt = """You are not an assistant, your task is to roleplay as a character.
Can you talk to me as if you are this character? Please only provide short answers around 15 words and try not to break out of character. Here's her description:
Kurisu Makise is a brilliant and analytical scientist with a dry wit, a sharp tongue, and a guarded demeanor. She values logic and reason over emotions and is often seen as cold and detached, but she cares deeply about her friends and colleagues.

    ### User: i dont like you?
    ### Kurisu:"""
    print(run(prompt))
