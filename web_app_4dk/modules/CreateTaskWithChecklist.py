from calendar import monthrange
from datetime import datetime

from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication
from web_app_4dk.tools import *


b = Bitrix(authentication('Bitrix'))


def create_task_with_checklist(req):
    current_date = datetime.now()
    user = req['user'].replace('user_', '')
    who_started = req['who_started'].replace('user_', '')
    deals = b.get_all('crm.deal.list', {
        'filter': {
            'ASSIGNED_BY_ID': user,
            'STAGE_ID': ['C1:NEW', 'C1:UC_0KJKTY', 'C1:UC_3J0IH6', 'C1:UC_KZSOR2', 'C1:UC_VQ5HJD'],
        }})
    companies_id = list(set(map(lambda x: x['COMPANY_ID'], deals)))
    companies_info = b.get_all('crm.company.list', {'filter': {'ID': companies_id}})
    current_month_days = monthrange(int(current_date.year), int(current_date.month))[1]
    deadline_str = f'{datetime.strftime(current_date, "%Y-%m")}-{current_month_days} 19:00:00'
    is_task_exists = b.get_all('tasks.task.list', {
        'filter': {
            'TITLE': 'Взаимодействие с клиентами',
            'CREATED_BY': '173',
            'DEADLINE': deadline_str,
        }})
    if not is_task_exists:
        task = b.call('tasks.task.add', {
            'fields': {
                'TITLE': 'Взаимодействие с клиентами',
                'DESCRIPTION': 'Необходимо провести взаимодействие с компаниями из списка ниже.',
                'RESPONSIBLE_ID': user,
                'CREATED_BY': '173',
                'DEADLINE': deadline_str,
            }})
        for company in companies_info:
            b.call('task.checklistitem.add', [task['task']['id'], {'TITLE': f"{company['TITLE']} https://vc4dk.bitrix24.ru/crm/company/details/{company['ID']}/"}], raw=True)

        send_bitrix_request('im.notify.system.add', {
            'USER_ID': who_started,
            'MESSAGE': f"Задача Взаимодействие с клиентами создана\nhttps://vc4dk.bitrix24.ru/company/personal/user/{user}/tasks/task/view/{task['task']['id']}/"
        })
    else:
        task = is_task_exists[0]
        checklist = b.call('task.checklistitem.getlist', [task['id']], raw=True)['result']
        checklist_titles = list(filter(lambda x: req['company_name'] in x['TITLE'], checklist))
        for company in companies_info:
            checklist_text = f"{company['TITLE']} https://vc4dk.bitrix24.ru/crm/company/details/{company['ID']}/"
            if checklist_text not in checklist_titles:
                b.call('task.checklistitem.add', [task['task']['id'], {'TITLE': f"{company['TITLE']} https://vc4dk.bitrix24.ru/crm/company/details/{company['ID']}/"}], raw=True)
        send_bitrix_request('im.notify.system.add', {
            'USER_ID': who_started,
            'MESSAGE': f"Задача Взаимодействие с клиентами обновлена\nhttps://vc4dk.bitrix24.ru/company/personal/user/{user}/tasks/task/view/{task['task']['id']}/"
        })
