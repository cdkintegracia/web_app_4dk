from fast_bitrix24 import Bitrix

from web_app_4dk.authentication import authentication

# Считывание файла authentication.txt

webhook = authentication('Bitrix')
b = Bitrix(webhook)



def check_task_result(dct):
    id = dct['id']
    task = b.get_all('tasks.task.list', {'params': {'WITH_RESULT_INFO': 'true'}, 'select': ['ID'], 'filter': {'ID': id}})[0]
    print(task)
    if task['taskHasResult'] == 'N':
        b.call('tasks.task.update', {'taskId': task['id'], 'fields': {'STAGE_ID': '1117'}})
        b.call('tasks.task.renew', {'taskId': task['id']})
