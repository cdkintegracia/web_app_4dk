import requests

webhook = 'https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/'

r = requests.get(url=f"{webhook}tasks.task.list?")
