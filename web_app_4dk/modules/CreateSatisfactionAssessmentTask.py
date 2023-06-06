from datetime import datetime, timedelta

from fast_bitrix24 import Bitrix

try:
    from authentication import authentication
except ModuleNotFoundError:
    from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def create_satisfaction_assessment_task(req):
    task_info = b.get_all('tasks.task.get', {
        'taskId': req['task_id'],
        'select': ['*', 'UF_*']
    })['task']
    uf_crm_task = task_info['ufCrmTask']
    uf_crm_company = list(filter(lambda x: 'CO_' in x, uf_crm_task))
    if not uf_crm_company:
        return

    company_id = uf_crm_company[0][3:]
    company_info = b.get_all('crm.company.get', {
        'ID': company_id,
        'select': ['TITLE', 'ASSIGNED_BY_ID'],
    })
    if company_info['ASSIGNED_BY_ID'] != '169':
        return

    ticket_date = (datetime.fromisoformat(task_info['createdDate'])).strftime('%d.%m.%Y')
    b.call('tasks.task.add', {
        'fields': {
            'TITLE': f'Оценка удовлетворенности ТЛП - {company_info["TITLE"]} - {ticket_date}',
            'DESCRIPTION': f'Завершенная задача: https://vc4dk.bitrix24.ru/workgroups/group/1/tasks/task/view/{task_info["id"]}/',
            'RESPONSIBLE_ID': '169',
            'DEADLINE': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
            'UF_CRM_TASK': task_info['ufCrmTask'],
            'CREATED_BY': '173',
        }
    })
