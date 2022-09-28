import requests

webhook = 'https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/'

task = requests.post(f"{webhook}tasks.task.get?taskId=56811").json()['result']

print(task['task']['status'])