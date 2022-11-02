import requests

webhook = 'https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/'
data = {'taskId': '77911'}
r = requests.post(url=f"{webhook}tasks.task.get", json=data).json()['result']
print(r)