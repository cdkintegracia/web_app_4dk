from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def fill_request_task_company(req):
    if 'company_id' in req:
        b.call('tasks.task.update', {
            'taskId': req['task_id'],
            'fields': {
                'UF_CRM_TASK': ['CO_' + req['company_id']]
            }
        })
