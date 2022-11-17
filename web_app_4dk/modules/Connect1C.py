import json

import requests
from fast_bitrix24 import Bitrix
import dateutil.parser
from datetime import timedelta
from requests.auth import HTTPBasicAuth  # or HTTPDigestAuth, or OAuth1, etc.
from requests import Session
from zeep import Client
from zeep.transports import Transport

from web_app_4dk.modules.authentication import authentication
from web_app_4dk.modules.UpdateCallStatistic import update_element


b = Bitrix(authentication('Bitrix'))

# Клиент для XML запроса
session = Session()
session.auth = HTTPBasicAuth('bitrix', 'SekXd4')
client = Client('https://cus.buhphone.com/cus/ws/PartnerWebAPI2?wsdl',
                transport=Transport(session=session))

# Словарь кодов 1с-коннект
connect_codes = {
    1: 'Текстовое сообщение',
    17: 'Оценка работы специалиста',
    20: 'Начало звонка с открытием обращения',
    21: 'Начало звонка без открытия обращения',
    22: 'Удачное завершение звонка',
    23: 'Неудачное завершение звонка. Вызов отменен инициатором',
    24: 'Неудачное завершение звонка. Абонент не ответил',
    25: 'Неудачное завершение звонка. Нет свободных специалистов',
    26: 'Неудачное завершение звонка. Вызов отклонен адресатом',
    27: 'Перевод звонка на специалиста',
    28: 'Перевод звонка в компанию вендора',
    30: 'Перевод звонка без завершения (когда абонент не взял трубку, а сразу перевел звонок)',
    31: 'Перевод звонка без завершения на вендора (когда абонент не взял трубку, а сразу перевел звонок)',
    32: 'Нет соединения с голосовым сервером',
    36: 'Неудачное завершение. У абонента нет аудио устройства',
    38: 'Недоступная линия по звонку (нерабочее время)',
    70: 'Файл',
    50: 'Начало сеанса удаленного доступа с сервисным специалистом',
    51: 'Начало сеанса удаленного доступа без сервисного специалиста (Специалист принудительно назначается пользователю сеансом удаленного доступа)',
    52: 'Окончание сеанса удаленного доступа с передачей файлов',
    53: 'Окончание сеанса удаленного доступа без передачей файлов',
    54: 'Неудачное завершение удаленного доступа. Сеанс отменен инициатором',
    55: 'Неудачное завершение удаленного доступа. Сеанс отклонен принимающим',
    56: 'Неудачное завершение удаленного доступа. Сеанс не состоялся по таймауту',
    57: 'Неудачное завершение удаленного доступа',
    59: 'Неудачное завершение - устаревшая версия службы',
    60: 'Неудачное завершение - служба не установлена',
    61: 'Неудачное завершение - устаревшие версии компонентов',
    62: 'Неудачное завершение - отсутствуют файлы компонентов УД',
    80: 'Начало обращения. Инициатор пользователь',
    81: 'Начало обращения. Инициатор специалист',
    82: 'Завершение работы специалиста (Закрытие обращения)',
    83: 'Обращение поступило в очередь. Нет свободных специалистов',
    84: 'Перевод обращения на специалиста',
    85: 'Перевод обращения в компанию вендора',
    86: 'Для обращения в очереди появился свободный специалист',
    87: 'Недоступность линии (нерабочее время)',
    88: 'Недоступность линии по переводу. При переводе обращения в компанию вендора попали в нерабочее время',
    89: 'Перевод в другую линию поддержки',
    90: 'Обращение закрыто автоматически по отсутствию активности в чате',
    91:  'Обращение закрыто автоматически, т.к. удалена линия поддержки',
    92: 'Обращение закрыто автоматически, т.к. удалена подписка пользователя',
    93: 'Обращение закрыто автоматически, т.к. удален пользователь',
    200: 'Перевод обращения специалистом на бота',
}


allow_id = ['127', '129', '131', '183', '1', '311', '125', '119', '123', '121']



def get_support_line_name(req):
    lines = client.service.ServiceLineKindRead('Params')[1]['Value']['row']
    if 'data' in req:
        if 'line_id' in req['data']:
            for line in lines:
                if req['data']['line_id'] == line['Value'][0]:
                    return line['Value'][2]
    else:
        for line in lines:
            if req['line_id'] == line['Value'][0]:
                return line['Value'][2]


def create_task(req) -> dict:
    # Создание задачи с первым сообщением
    data = load_logs()
    task_text = ''
    for event in data[::-1]:
        if event['treatment_id'] == req['treatment_id'] and event['message_type'] == 1:
            task_text = event['text']
            break

    # Проверка на наличие хотя бы одного русского символа в сообщении
    russian_char_flag = False
    for word in task_text:
        for char in word:
            if 1040 <= ord(char) <= 1103:
                russian_char_flag = True
    if russian_char_flag is False:
        return {'error': 'Нет хотя бы одного русского символа в сообщении'}

    # Проверка сообщения через фильтр
    filter_word_list = [
        'спасибо',
    ]
    if task_text.lower().strip('!-_/|\\+,.? ') in filter_word_list:
        return {'error': 'сообщение попало в фильтр лист'}

    # Проверка на инициатора обращения
    author_info = get_name(event['author_id'], req['treatment_id'])
    is_author_support = get_employee_id(author_info[0])
    if is_author_support != '0':
        return {'error': 'Инициатор сообщения - сотрудник'}

    message_time = time_handler(req['message_time'])
    user_info = get_name(req['user_id'], req['treatment_id'])
    if len(author_info) < 2:
        company_id = user_info[1]
    else:
        company_id = author_info[1]

    support_info = get_name(req['author_id'], req['treatment_id'])
    support_id = get_employee_id(support_info[0])
    responsible_id = '173'
    if support_id in allow_id:
        responsible_id = support_id
    support_line_name = get_support_line_name(req)
    if 'ЛК' in support_line_name:
        new_task = send_bitrix_request('tasks.task.add', {'fields': {
            'TITLE': f"1С:Коннект {support_line_name}",
            'DESCRIPTION': f"{message_time} {author_info[0]}\n{task_text}",
            'GROUP_ID': '7',
            'CREATED_BY': '173',
            'RESPONSIBLE_ID': responsible_id,
            'UF_CRM_TASK': [f"CO_{company_id}"],
            'UF_AUTO_499889542776': req['treatment_id'],
            'STAGE_ID': '65'
        }})
        return new_task['task']
    new_task = send_bitrix_request('tasks.task.add', {'fields': {
        'TITLE': f"1С:Коннект {support_line_name}",
        'DESCRIPTION': f"{message_time} {author_info[0]}\n{task_text}",
        'GROUP_ID': '75',
        'CREATED_BY': '173',
        'RESPONSIBLE_ID': responsible_id,
        'UF_CRM_TASK': [f"CO_{company_id}"],
        'UF_AUTO_499889542776': req['treatment_id'],
        'STAGE_ID': '1165',
    }})
    return new_task['task']


def check_task_existence(req) -> dict:
    data = {
        'select': ['*', 'UF_*'],
        'filter': {
            'UF_AUTO_499889542776': req['treatment_id']
        }
    }
    task_existence = send_bitrix_request('tasks.task.list', data)['tasks']
    if not task_existence:
        return create_task(req)
    else:
        return task_existence[0]


def send_bitrix_request(method: str, data: dict):
    return requests.post(f"{authentication('Bitrix')}{method}", json=data).json()['result']


def load_logs():
    logs = []
    with open('/root/web_app_4dk/web_app_4dk/static/logs/connect_logs.txt') as file:
        for line in file:
            logs.append(json.loads(line))
    return logs


def time_handler(time: str) -> str:
    time = dateutil.parser.isoparse(time)
    time += timedelta(hours=3)
    message_time = f"{time.hour}:{time.minute}:{time.second} {time.day}.{time.month}.{time.year}"
    return message_time


def get_employee_id(name: str) -> str:
    name = name.split()
    employee_id = send_bitrix_request('user.get', {'filter': {'NAME': name[0], 'LAST_NAME': name[1]}})
    try:
        return employee_id[0]['ID']
    except:
        return '0'


def get_event_info(event: dict) -> str:
    if event['message_type'] == 1:
        return f"{event['text']}\n"
    if event['message_type'] == 53:
        return f"Длительность: {event['rda']['duration']}\n"
    if event['message_type'] == 70:
        if 'preview_link_hi' in event['file']:
            return f"{event['file']['file_name']}\n{event['file']['preview_link_hi']}\n"
        else:
            return f"{event['file']['file_name']}\n{event['file']['file_path']}\n"
    if event['message_type'] == 82:
        return f"Длительность обращения: {event['treatment']['treatment_duration']}\n"
    return f"\n"


def get_name(user_id: str, *args) -> list:

    # Получение списка сотрудников
    specialists = client.service.SpecialistRead('Params')
    for specialist in specialists[1]['Value']['row']:
        if user_id == specialist['Value'][0]:
            user_name = f"{specialist['Value'][3]} {specialist['Value'][4]}"
            return [user_name]

    # Получение списка сотрудников компании-клиента
    company_users = client.service.ClientUserRead('Params')

    # Получение списка компаний-клиентов
    companies = client.service.ClientRead('Params')

    # Сопоставление клиента и компании, к которой он относится
    for user in company_users[1]['Value']['row']:
        if user_id == user['Value'][0]:
            company_id = user['Value'][1]
            user_name = f"{user['Value'][4]} {user['Value'][5]}"
            for company in companies[1]['Value']['row']:
                if company_id == company['Value'][0]:
                    inn = company['Value'][4]
                    try:
                        company_id = send_bitrix_request('crm.company.list', {'select': ['ID'], 'filter': {'UF_CRM_1656070716': inn}})[0]['ID']
                    except:
                        send_bitrix_request('tasks.task.add', {
                            'fields': {
                                'TITLE': '1С:Коннект Не найдена компания по ИНН',
                                'DESCRIPTION': f"ID компании: {company_id}\nИНН: {inn}\nID обращения: {args[0]}",
                                'CREATED_BY': '173',
                                'RESPONSIBLE_ID': '173',
                                'GROUP_ID': '75',
                                'STAGE_ID': '0',
                            }})
                        company_id = '12'
                    return [user_name, company_id]


def connect_1c(req: dict):
    if req['event_type'] != 'line':
        return
    # Запись события в логи
    with open('/root/web_app_4dk/web_app_4dk/static/logs/connect_logs.txt', 'a') as file:
        json.dump(req, file, ensure_ascii=False)
        file.write('\n')

    # Новое обращение
    if req['message_type'] == 80:
        task = check_task_existence(req)
        if 'error' in task:
            return

    # Перевод обращения
    if req['message_type'] == 89 and req['data']['direction'] == 'to':
        task = check_task_existence(req)
        if 'error' in task:
            return
        support_line_name = get_support_line_name(req)
        if 'ЛК' in support_line_name:
            send_bitrix_request('tasks.task.update', {
                'taskId': task['id'],
                'fields': {
                    'UF_AUTO_499889542776': req['data']['treatment_id'],
                    'GROUP_ID': '7',
                    'STAGE_ID': '65'
                }})
        else:
            send_bitrix_request('tasks.task.update', {
                'taskId': task['id'],
                'fields': {
                    'UF_AUTO_499889542776': req['data']['treatment_id']
                }})

    # Завершение обращения. Закрытие задачи
    elif req['message_type'] in [82, 90, 91, 92, 93]:
        task = check_task_existence(req)
        if 'error' in task:
            return
        task_text = ''
        treatment_id = req['treatment_id']
        authors = {}
        data = load_logs()
        event_count = 0
        for event in data:
            if event['treatment_id'] == treatment_id and event['message_type'] not in [80, 81]:
                event_count += 1
                if event_count < 2:
                    continue
                if event['author_id'] not in authors:
                    authors.setdefault(event['author_id'], get_name(event['author_id']))
                task_text += f"{time_handler(event['message_time'])} {authors[event['author_id']][0]}\n{connect_codes[event['message_type']]}\n"
                task_text += f"{get_event_info(event)}\n"

        support_line_name = get_support_line_name(req)
        if 'ЛК' in support_line_name:
            send_bitrix_request('tasks.task.update',
                                {'taskId': task['id'], 'fields': {'GROUP_ID': '7', 'STAGE_ID': '67', 'STATUS': '5'}})
        else:
            send_bitrix_request('tasks.task.update',
                                {'taskId': task['id'], 'fields': {'STAGE_ID': '1167', 'STATUS': '5'}})
        task_comments = requests.get(f'{authentication("Bitrix")}task.commentitem.getlist?ID={task["id"]}').json()['result']
        for comment in task_comments:
            params = {0: task['id'], 1: comment['ID']}
            requests.post(f"{authentication('Bitrix')}task.commentitem.delete", json=params)
        b.call('task.commentitem.add', [task['id'], {'POST_MESSAGE': task_text, 'AUTHOR_ID': task['responsibleId']}], raw=True)
        elapsed_time = req['treatment']['treatment_duration']
        b.call('task.elapseditem.add', [task['id'], {'SECONDS': elapsed_time, 'USER_ID': '173'}], raw=True)
        ufCrmTask = task['ufCrmTask']
        company_id = list(filter(lambda x: 'CO' in x, ufCrmTask))[0].replace('CO_', '')
        update_element(company_id=company_id, connect_treatment=True)

    # Смена ответственного
    data = {
        'filter':
            {'UF_AUTO_499889542776': req['treatment_id']}
    }
    task = send_bitrix_request('tasks.task.list', data)['tasks']
    if not task:
        return
    else:
        task = task[0]
    data = {'taskId': task['id']}
    task = send_bitrix_request('tasks.task.get', data)['task']
    connect_user_name = get_name(req['author_id'])[0]
    connect_user_id = get_employee_id(connect_user_name)
    if str(connect_user_id) in allow_id:
        task_user_name = task['responsible']['name']
        if task_user_name != connect_user_name:
            data = {'taskId': task['id'], 'fields': {'RESPONSIBLE_ID': connect_user_id, 'AUDITORS': []}}
            requests.post(url=f"{authentication('Bitrix')}tasks.task.update", json=data)
