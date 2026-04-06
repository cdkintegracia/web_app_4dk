from fast_bitrix24 import Bitrix
from web_app_4dk.modules.authentication import authentication


webhook = authentication('Bitrix')
b = Bitrix(webhook)

def task_test_vip(req):
    task_id = req['task_id']
    task_info = b.get_all('tasks.task.get', { # читаем инфо о задаче
        'taskId': task_id,
        'select': ['*', 'UF_*', 'TAGS']
    })

    tags = task_info['task']['tags']

    try:
        has_vip = any(tag['title'] == 'VIP' for tag in tags.values())
        if has_vip:
            print('Есть тег VIP')
        else:
            print('Тега VIP нет')
    except:
        print('Тега VIP нет')

    try:
        print(tags)
        #print(task_info['task']['tags'])
    except:
        print(task_info)
        print(2)