from fast_bitrix24 import Bitrix
from authentication import authentication

# Считывание файла authentication.txt

webhook = authentication('Bitrix')
b = Bitrix(webhook)


def check_task_result(dct):
    id = dct['id']
    task = b.get_all('tasks.task.list', {'params': {'WITH_RESULT_INFO': 'true'}, 'filter': {'ID': id}})
    print(task)