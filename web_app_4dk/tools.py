import base64

import requests

from web_app_4dk.modules.authentication import authentication



def send_bitrix_request(method: str, data: dict):
    try:
        return requests.post(f"{authentication('Bitrix')}{method}", json=data).json()['result']
    except KeyError:
        return
