from datetime import datetime

from fast_bitrix24 import Bitrix
from authentication import authentication
#from web_app_4dk.modules.authentication import authentication

b = Bitrix(authentication('Bitrix'))


def create_tasks_active_sales(req):
    count = 0
    task_text = b.get_all('tasks.task.get', {'taskId': req['task_id']})['task']['description']
    task_text = task_text.replace('[P]', '').replace('[/P]', '')
    companies_id = req['companies_id'].split(' ')
    companies_info = b.get_all('crm.company.list', {'filter': {'ID': companies_id}})
    for company in companies_info:
        responsible_id = '405'
        if count % 2 == 0:
            responsible_id = '403'
        count += 1
        b.call('tasks.task.add', {
            'fields': {
                'TITLE': f"Проработка",
                'DESCRIPTION': task_text,
                'RESPONSIBLE_ID': '311',
                'CREATED_BY': '173',
                'DEADLINE': f"{datetime.strftime(datetime.now(), '%Y-%m-%d')} 19:00",
                'UF_CRM_TASK': ['CO_' + company['ID']],
                'GROUP_ID': '101',
            }})
        exit()

    b.call('im.notify.system.add', {
        'USER_ID': '1',
        'MESSAGE': 'Задачи на активные продажи поставлены'})

