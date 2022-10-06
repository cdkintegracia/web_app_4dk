from fast_bitrix24 import Bitrix
import requests

b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')

tasks = b.get_all('tasks.task.list', {'filter': {'>CREATED_DATE': '2022-09-23'}})

for task in tasks:
    b.call('task.commentitem.add', [task['id'], {'POST_MESSAGE': '.'}], raw=True)

