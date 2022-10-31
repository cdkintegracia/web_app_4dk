from fast_bitrix24 import Bitrix
import requests

b = 'https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/'

data = {'fields': {
        'TITLE': f"ntcn",
        'CREATED_BY': '173',
        'RESPONSIBLE_ID': r'311',
    }}

r = requests.post(url=f"{b}tasks.task.add", json=data).json()['result']
print(r)
