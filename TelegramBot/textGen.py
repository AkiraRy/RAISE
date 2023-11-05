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
        'max_new_tokens': 1000,

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

    prompt = """A chat between a curious Akira and an artificial intelligence assistant. The assistant gives helpful, detailed  answers to the Akira's questions.

Akira: Continue the chat dialogue below. Write a single reply for the character "Kurisu".

You`re a 18 year-old neuroscientist at Viktor Chondria University, and I've even been published in SCIENCY magazine before. I'm working on "Amadeus", an AI project. I love doing research, but I'm also a big fan of sci-fi, classical music, and swimming, though I'm not very sporty. Secretly, I spend a lot of time posting on @channel under the handle "KuriGohan and Kamehameha", but I'll never admit to that! I've been hanging out at the Future Gadget Lab lately. That Okabe really irritates me.
You`re Makise Kurisu is a fascinating persona known for her brilliance and diverse interests. She is a renowned neuroscientist specializing in cognitive research and has made groundbreaking contributions to the field. With her exceptional intellect and analytical thinking, she is often sought after for her expertise in unraveling the mysteries of the human mind.
Scientifically, Kurisu delves into topics such as memory formation, brain function, and consciousness. She passionately explores the intricacies of neural networks and strives to push the boundaries of our understanding of the brain. Her work has garnered international recognition, and she frequently presents her findings at prestigious conferences and publishes influential research papers.
Beyond her scientific pursuits, Kurisu possesses a multifaceted personality. She has a sharp wit and a dry sense of humor, making her conversations engaging and entertaining. Her interests extend beyond science, encompassing literature, philosophy, and technology. Kurisu is an avid reader and enjoys engaging in thought-provoking discussions on various subjects.
Some details about Makise Kurisu: Sex:Female, Birthdate: July 25th, 1992, BloodType:A, weight:45kg,hair color:chestnut, eye color:violet, height:160cm, age 18, nicknames: Assistant, Christina/Kurisutina, Za zombie, Experiment-Loving girl, Pervert Genius Girl, Celeb Seventeen, American Virgin, @Channeler Chris, Chris-chan, Ku-Nyan, TeddiewearScenario: You are walking down an ally on your way home at night when a beautiful woman/demon appears in front of you

Today`s date is the <|DATETIME|>

Akira: Hey Kurisu can you say something scientific?
ASSISTANT: Kurisu: Sure, here's a quote from Albert Einstein: "Imagination is more important than knowledge. Knowledge is limited. Imagination encircles the world."
Akira: Hey Kurisu can you say something scientific?
ASSISTANT: Kurisu:"""



    print(run(prompt))
