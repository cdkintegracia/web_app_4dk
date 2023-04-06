from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication

b = Bitrix(authentication('Bitrix'))

def change_task_created_by(req):
    b.call('tasks.task.update', {
        'taskId': req['task_id'],
        'fields': {
            'CREATED_BY': req['new_created_by']
        }
    })
    print(req['new_created_by'])