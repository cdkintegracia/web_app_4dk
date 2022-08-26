from fast_bitrix24 import Bitrix

from web_app_4dk.authentication import authentication

# Считывание файла authentication.txt
webhook = authentication('Bitrix')
b = Bitrix(webhook)



def check_task_result(dct):
    id = dct['id']
    task = b.get_all('task.commentitem.getlist', {'ID': id})
    for comment in task:
        if '[USER=333]' in comment['POST_MESSAGE']:
            return
    b.call('tasks.task.update', {'taskId': id, 'fields': {'STAGE_ID': '1121'}})



