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

    '''
    if task_info['groupId']=='1' and task_info['stageId']=='11':
        try:
            has_vip = any(tag['title'] == 'VIP' for tag in tags.values())
            if has_vip:
                print('Есть тег VIP')
            else:
                print('Тега VIP нет')
        except:
            print('Тега VIP нет')
    '''

    try:
        has_vip = any(tag['title'] == 'VIP' for tag in tags.values())
    except:
        has_vip = False

    if has_vip == False:
        print('Тега VIP нет')
    else:
        print('Есть тег VIP')