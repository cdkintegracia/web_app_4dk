from datetime import timedelta, datetime

from fast_bitrix24 import Bitrix
import gspread
import dateutil.parser
import requests

from web_app_4dk.modules.authentication import authentication
from web_app_4dk.modules.UpdateEmailStatistic import update_email_statistic
from web_app_4dk.tools import *

webhook = authentication('Bitrix')
b = Bitrix(webhook)


def get_user_name(user_id: str):
    return
    user_info = b.get_all('user.get', {'ID': user_id})[0]
    return f"{user_info['NAME']} {user_info['LAST_NAME']}"


def write_to_sheet(data: list):
    """
    Запись данных в Google Sheet
    :param data: Данные о событии
    :return:
    """
    access = gspread.service_account(f"/root/credentials/bitrix24-data-studio-2278c7bfb1a7.json")
    spreadsheet = access.open('bitrix_data')
    worksheet = spreadsheet.worksheet('user_statistics')
    worksheet.insert_row(data, index=2)


def time_handler(time: str) -> str:
    """
    Форматирование времени
    :param time: время в формате '2022-09-21T14:30:13+03:00'
    :return: дата в формате '01.01.2021'
    """
    time = dateutil.parser.isoparse(time)
    message_time = f"{time.day}.{time.month}.{time.year}"
    return message_time


def add_call(req: dict):
    """
    Фильтр звонка по коду ошибки, получение имени и фамилии сотрудника
    :param req: request.form
    :return:
    """
    if req['data[CALL_FAILED_CODE]'] != '200':
        return
    user_info = b.get_all('user.get', {'ID': req['data[PORTAL_USER_ID]']})[0]
    user_name = f"{user_info['NAME']} {user_info['LAST_NAME']}"
    data_to_write = [
        req['data[CALL_ID]'],
        'CALL',
        user_name,
        time_handler(req['data[CALL_START_DATE]']),
        req['data[CALL_TYPE]'],
        req['data[CALL_DURATION]']
    ]
    write_to_sheet(data_to_write)


def add_mail(req: dict):
    """
    Фильтр события по его типу (EMAIL), получение подробной информации по его ID
    :param req: request.form
    :return:
    """
    activity_type = requests.post(f"{authentication('Bitrix')}crm.activity.get?id={req['data[FIELDS][ID]']}").json()
    if activity_type['result']['PROVIDER_TYPE_ID'] == 'EMAIL':
        update_email_statistic(activity_type['result'])
        user_info = b.get_all('user.get', {'ID': activity_type['result']['AUTHOR_ID']})[0]
        user_name = f"{user_info['NAME']} {user_info['LAST_NAME']}"
        data_to_write = [activity_type['result']['ID'],
            'EMAIL',
                         user_name,
                         time_handler(activity_type['result']['CREATED']),
                         'Отправлено']
        write_to_sheet(data_to_write)


def add_new_task(req: dict):
    data = {
        'select': ['UF_CRM_TASK', 'GROUP_ID', 'RESPONSIBLE_ID', 'CREATED_DATE'],
        'taskId': req['data[FIELDS_AFTER][ID]']
    }
    task = send_bitrix_request('tasks.task.get', data)
    if 'ufCrmTask' not in task['task'] or 'groupId' not in task['task']:
        return
    uf_crm_task = task['task']['ufCrmTask']
    if not uf_crm_task:
        return
    company = list(filter(lambda x: 'CO' in x, uf_crm_task))
    if not company:
        return
    company = company[0]
    data = {
        'filter': {
            'ID': company.replace('CO_', '')
        }}
    company_name = send_bitrix_request('crm.company.list', data)[0]['TITLE']
    task_id = task['task']['id']
    group_id = task['task']['groupId']
    group_name = task['task']['group']['name']
    responsible = task['task']['createdBy']
    created_date = dateutil.parser.isoparse(task['task']['createdDate'])
    date_start_filter = datetime.strftime(created_date - timedelta(hours=1), '%Y-%m-%d %H:%M:%S')

    data = {
        'filter': {
            '>=CREATED_DATE': date_start_filter,
            'GROUP_ID': group_id,
            'UF_CRM_TASK': company
        }}
    check_tasks = send_bitrix_request('tasks.task.list', data)['tasks']

    if len(check_tasks) > 1:
        task_urls = ''
        for check_task in check_tasks:
            if check_task['id'] == task_id:
                continue
            task_urls += f'https://vc4dk.bitrix24.ru/workgroups/group/{group_id}/tasks/task/view/{check_task["id"]}/\n'
        data = {
            'USER_ID': responsible,
            'MESSAGE': f'ВНИМАНИЕ! В течение последнего часа для {company_name} уже была создана задача в {group_name}.\n' 
                       f'{task_urls}'
        }
        send_bitrix_request('im.notify.system.add', data)


def add_old_task(req: dict):
    try:
        task = requests.get(f"{authentication('Bitrix')}tasks.task.get?taskId={req['data[FIELDS_AFTER][ID]']}").json()['result']
        if task:
            if task['task']['status'] != '5':
                return
        user_info = requests.get(f"{authentication('Bitrix')}user.get?id={task['task']['responsibleId']}").json()
        user_info = user_info['result'][0]
        user_name = f"{user_info['NAME']} {user_info['LAST_NAME']}"
        data_to_write = [task['task']['id'],
                         'TASK',
                         user_name,
                         time_handler(task['task']['createdDate']),
                         'Завершена'
                         ]
    except:
        return
    write_to_sheet(data_to_write)


def update_user_statistics(req: dict):
    """
    Вызывает нужную функция для переданного типа события
    :param req: request.form
    :return:
    """
    funcs = {
        'ONVOXIMPLANTCALLEND': add_call,
        'ONCRMACTIVITYADD': add_mail,
        'ONTASKADD': add_new_task,
        'ONTASKUPDATE': add_old_task,
    }
    if 'event' in req:
        funcs[req['event']](req)






