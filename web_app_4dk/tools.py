import base64

import requests

from web_app_4dk.modules.authentication import authentication



def send_bitrix_request(method: str, data: dict):
    req = requests.post(f"{authentication('Bitrix')}{method}", json=data).json()
    if 'result' in req:
        return req['result']
    return req

