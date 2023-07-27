import os
import time
from dotenv import load_dotenv
import requests
from pathlib import Path


load_dotenv()
BASE_URL = os.getenv('WHISPER_BASE_URL')


def transcribe(filepath):
    start_time = time.time()
    try:
        with open(filepath, 'rb') as infile:
            files = {'audio_file': infile}
            print('before request')
            print(f'{filepath} {BASE_URL}')
            r = requests.post(f'{BASE_URL}/asr?task=transcribe&language=en&output=json', files=files)

    except requests.exceptions.Timeout:
        print('Request timeout')
        return None
    except requests.exceptions.ConnectionError:
        print('Unable to reach Whisper, ensure that it is running, or the WHISPER_BASE_URL variable is set correctly')
        return None

    end_time = time.time()
    execution_time = round(end_time - start_time, 2)
    print(f"\nTranscribed in {execution_time} seconds")  # maybe change this in future into json {time:time, data:data}
    # return {'time':execution_time, 'data':r.json()['text'].strip()}  #  Need to fix in other file handling this
    return r.json()['text'].strip()


AUDIO_DIR = Path(os.getenv('AUDIO_DIR'))
VOICE_FILE = os.getenv('VOICE_FILE')

if __name__ == '__main__':
    print(transcribe(AUDIO_DIR/VOICE_FILE))
