from datetime import datetime, timedelta

from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication
from web_app_4dk.tools import send_bitrix_request


b = Bitrix(authentication('Bitrix'))


def create_95_service_using_task(req):
    task_title = f"Для {req['company_name']} использование сервиса {req['service_name']} достигло 95% лимита"
    filter_date_start = datetime.now() - timedelta(days=1)
    filter_date_end = datetime.now() + timedelta(days=1)
    tasks = send_bitrix_request('tasks.task.list', {
        'filter': {
            'TITLE': task_title,
            '>CREATED_DATE': filter_date_start.strftime('%Y-%m-%d'),
            '<CREATED_DATE': filter_date_end.strftime('%Y-%m-%d')
        }
    })
    if not tasks:
        send_bitrix_request('tasks.task.add', {
            'fields': {
                'TITLE': task_title,
                'CREATED_BY': '173',
                'RESPONSIBLE_ID': '133',
                'UF_CRM_TASK': ['CO_' + req['company_id']]
            }
        })
