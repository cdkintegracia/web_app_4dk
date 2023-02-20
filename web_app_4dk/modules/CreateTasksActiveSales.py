from datetime import datetime

from fast_bitrix24 import Bitrix

#from authentication import authentication
from web_app_4dk.modules.authentication import authentication

b = Bitrix(authentication('Bitrix'))


def create_tasks_active_sales(req):
    departments = b.get_all('department.get')
    users = b.get_all('user.get')
    department_heads = list(map(lambda x: x['UF_HEAD'] if 'UF_HEAD' in x else '', departments))
    count = 0
    task_text = b.get_all('tasks.task.get', {'taskId': req['task_id']})['task']['description']
    task_text = task_text.replace('[P]', '').replace('[/P]', '')
    companies_id = req['companies_id'].split(' ')
    companies_info = b.get_all('crm.company.list', {'filter': {'ID': companies_id}})
    for company in companies_info:
        auditors = ['391', ]
        if company['ASSIGNED_BY_ID'] in department_heads:
            auditors.append(company['ASSIGNED_BY_ID'])
        else:
            user_info = list(filter(lambda x: x['ID'] == company['ASSIGNED_BY_ID'], users))
            user_department = str(user_info[0]['UF_DEPARTMENT'][0])
            user_department_head = list(filter(lambda x: x['ID'] == user_department, departments))
            print(user_info)
            auditors.append(user_department_head[0]['UF_HEAD'])
        responsible_id = '405'
        if count % 2 == 0:
            responsible_id = '403'
        count += 1
        '''
        b.call('tasks.task.add', {
            'fields': {
                'TITLE': f"Проработка",
                'DESCRIPTION': task_text,
                'RESPONSIBLE_ID': responsible_id,
                'CREATED_BY': '173',
                'DEADLINE': f"{datetime.strftime(datetime.now(), '%Y-%m-%d')} 19:00",
                'UF_CRM_TASK': ['CO_' + company['ID']],
                'GROUP_ID': '101',
                'AUDITORS': auditors,
            }})

    b.call('im.notify.system.add', {
        'USER_ID': '1',
        'MESSAGE': 'Задачи на активные продажи поставлены'})
    '''
