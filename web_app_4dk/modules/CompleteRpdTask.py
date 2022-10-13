from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication

# Считывание файла authentication.txt

webhook = authentication('Bitrix')
b = Bitrix(webhook)


def complete_rpd_task(req):
    task = b.get_all('tasks.task.get', {'taskId': req['id']})
    print(task)
    