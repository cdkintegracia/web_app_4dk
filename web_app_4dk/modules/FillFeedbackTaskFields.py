from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def fill_feedback_task_fields(req):
    task_id = req['form_url'].split('task_id=')[1]
    task_update = b.call('tasks.task.update', {
        'taskId': task_id,
        'fields': {
            'UF_AUTO_177856763915': req['rating'],
            'UF_AUTO_917673898341': req['commentary']
        }
    })
