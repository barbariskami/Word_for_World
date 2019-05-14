import time
import jwt
import requests

service_account_id = "ajem4vc8glviavjskhl4"
key_id = "ajehjmo7maie9e5kpkhr"  # ID ресурса Key, который принадлежит сервисному аккаунту.
FOLDER_ID = 'b1gg89gfd3p1ukm7njal'


def update_iam():
    with open("private_key.pem", 'r') as private:
        private_key = private.read()  # Чтение закрытого ключа из файла.

    now = int(time.time())
    payload = {
        'aud': 'https://iam.api.cloud.yandex.net/iam/v1/tokens',
        'iss': service_account_id,
        'iat': now,
        'exp': now + 360}

    # Формирование JWT.
    encoded_token = jwt.encode(
        payload,
        private_key,
        algorithm='PS256',
        headers={'kid': key_id})

    params = {'jwt': encoded_token}

    req = 'https://iam.api.cloud.yandex.net/iam/v1/tokens'
    response = requests.post(req, params=params)
    IAM_TOKEN = response.json()['iamToken']
    return IAM_TOKEN


def synthesize(folder_id, iam_token, text):
    url = 'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'
    headers = {
        'Authorization': 'Bearer ' + iam_token,
    }

    data = {
        'text': text,
        'lang': 'en-US',
        'folderId': folder_id,
        'speed': 0.9,
        'voice': 'alyss'

    }

    with requests.post(url, headers=headers, data=data, stream=True) as resp:
        if resp.status_code != 200:
            raise RuntimeError("Invalid response received: code: %d, message: %s" % (resp.status_code, resp.text))

        for chunk in resp.iter_content(chunk_size=None):
            yield chunk


def make_audio(folder_id, token, text):
    with open('audio.ogg', "wb") as f:
        for audio_content in synthesize(folder_id, token, text):
            f.write(audio_content)
