from fast_bitrix24 import Bitrix

b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')

tasks = b.get_all('tasks.task.list', {
        'filter': {
            'GROUP_ID': '71',
            'REAL_STATUS': '5',
        }
    })

print(tasks)