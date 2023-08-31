from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication
from web_app_4dk.tools import send_bitrix_request


b = Bitrix(authentication('Bitrix'))


def complete_dossier_task(req):
    company_info = send_bitrix_request('crm.company.get', {
        'ID': req['company_id']
    })
    tasks = send_bitrix_request('tasks.task.list', {
        'filter': {
            'TITLE': f'Заполнить Досье на {company_info["TITLE"]}',
            '!STATUS': '5'
        }
    })['tasks']
    for task in tasks:
        send_bitrix_request('tasks.task.complete', {
            'id': task['id'],
            }
        )