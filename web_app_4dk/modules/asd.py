from fast_bitrix24 import Bitrix
import requests

b = 'https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/'

data = {
    'filter': {
        'UF_AUTO_499889542776': '0b6801df-bdb5-458b-9edd-85d703afcd17'
    }
}

r = requests.post(url=f"{b}tasks.task.list", json=data).json()['result']['tasks']
if r:
    print(r)
else:
    print('no')
