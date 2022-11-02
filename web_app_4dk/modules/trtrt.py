import requests

r = requests.post(url='https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/tasks.task.get', json={'taskId': '78083'}).json()
print(r)