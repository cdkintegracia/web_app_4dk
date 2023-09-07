import csv

from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication
from web_app_4dk.tools import send_bitrix_request


b = Bitrix(authentication('Bitrix'))


with open('ids.csv', 'r') as file:
    data = file.readlines()

for index, element_id in enumerate(map(str.strip, data)):
    if index == 0:
        continue
    element_info = send_bitrix_request('lists.element.get', {
        'IBLOCK_TYPE_ID': 'lists',
        'IBLOCK_ID': '107',
        'ELEMENT_ID': element_id
    })[0]
    task_id = list(element_info['PROPERTY_517'].values())[0]
    task_info = send_bitrix_request('tasks.task.get', {
        'taskId': task_id
    })['task']
    if task_info['groupId'] and task_info['groupId'] != '0':
        task_url = f'<a href="https://vc4dk.bitrix24.ru/workgroups/group/{task_info["groupId"]}/tasks/task/view/{task_info["id"]}/">Ссылка на задачу</a>'
    else:
        task_url = f'<a href="https://vc4dk.bitrix24.ru/company/personal/user/{task_info["responsibleId"]}/tasks/task/view/{task_info["id"]}/">Ссылка на задачу</a>'
    send_bitrix_request()