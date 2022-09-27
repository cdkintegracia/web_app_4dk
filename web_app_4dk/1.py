from fast_bitrix24 import Bitrix

b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')





is_task_created = b.get_all('tasks.task.list', {
        'select': ['ID', 'RESPONSIBLE_ID'],
        'filter': {
            'UF_AUTO_499889542776': 'c3445798-90b1-48a2-9ea6-c14362b314cc'}})
print(is_task_created[0]['responsible']['name'])