from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def fill_request_task_company(req):
    company_name = req['task_text'].split('\n')[1]
    company_info = b.get_all('crm.company.list', {
        'filter': {
            'TITLE': company_name,
        }
    })
    if not company_info:
        return
    company_id = company_info[0]['ID']
    b.call('tasks.task.update', {
        'taskId': req['task_id'],
        'fields': {
            'UF_CRM_TASK': ['CO_' + company_id]
        }
    })

