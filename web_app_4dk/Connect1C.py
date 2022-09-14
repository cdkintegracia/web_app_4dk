import json

from fast_bitrix24 import Bitrix
import dateutil.parser
from requests.auth import HTTPBasicAuth  # or HTTPDigestAuth, or OAuth1, etc.
from requests import Session
from zeep import Client
from zeep.transports import Transport

from web_app_4dk.authentication import authentication

b = Bitrix(authentication('Bitrix'))

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

def get_name(user_id):
    session = Session()
    session.auth = HTTPBasicAuth('bitrix', 'SekXd4')
    client = Client('https://cus.buhphone.com/cus/ws/PartnerWebAPI2?wsdl',
                    transport=Transport(session=session))

    specialists = client.service.SpecialistRead('Params')
    for specialist in specialists[1]['Value']['row']:
        if user_id == specialist['Value'][0]:
            user_name = f"{specialist['Value'][3]} {specialist['Value'][4]}"
            return [user_name]
    company_users = client.service.ClientUserRead('Params')
    companies = client.service.ClientRead('Params')
    for user in company_users[1]['Value']['row']:
        if user_id == user['Value'][0]:
            company_id = user['Value'][1]
            user_name = f"{user['Value'][4]} {user['Value'][5]}"
            for company in companies[1]['Value']['row']:
                if company_id == company['Value'][0]:
                    inn = company['Value'][4]
                    company_id = b.get_all('crm.company.list', {'select': ['ID'], 'filter': {'UF_CRM_1656070716': inn}})[0]['ID']
                    return [user_name, company_id]



def connect_1c(req):
    with open('/root/web_app_4dk/web_app_4dk/static/logs/connect.json', 'r') as file:
        data = json.load(file)
        data.append(req)

        with open('/root/web_app_4dk/web_app_4dk/static/logs/connect.json', 'w') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    if req['message_type'] == 1:
        user_info = get_name(req['user_id'])
        support_info = get_name(req['author_id'])

        b.call('tasks.task.add', {'fields': {
            'TITLE': f"Коннект",
            'DESCRIPTION': f"{user_info[0]} {support_info[0]} {user_info[1]}",
            'GROUP_ID': '13',
            'CREATED_BY': '173',
            'RESPONSIBLE_ID': '311',
            'UF_CRM_TASK': 'CO_' + user_info[1],
            'UF_AUTO_499889542776': req['treatment_id']
        }})


'''
    if req['message_type'] in [82, 90]:
        task_text = ''
        treatment_id = req['treatment_id']
        user_info = get_name(req['user_id'])
        support_info = get_name(req['author_id'])
        user_names = {
            req['user_id']: user_info[0],
            req['author_id']: support_info[0],
        }

        with open('/root/web_app_4dk/web_app_4dk/static/logs/connect.json', 'r') as file:
            data = json.load(file)
            for event in data:
                if event['treatment_id'] == treatment_id:
                    time = dateutil.parser.isoparse(event['message_time'])
                    message_time = f"{time.hour}:{time.minute}:{time.second} {time.day}.{time.month}.{time.year}"
                    task_text += f"{message_time} {connect_codes[event['message_type']]}\n"
                    if 'text' in event:
                        task_text += f"{event['text']}\n"
                    if 'rda' in event:
                        task_text += f"Длительность: {event['rda']['duration']} секунд\n"
                    if 'preview_link' in event:
                        task_text += f"{event['preview_link']}\n"
                    task_text += user_info[0]
                    task_text += support_info[0]
                    task_text += user_info[1]



        b.call('tasks.task.add', {'fields': {
            'TITLE': f"Коннект",
            'DESCRIPTION': task_text,
            'GROUP_ID': '13',
            'CREATED_BY': '173',
            'RESPONSIBLE_ID': '311',
        }})
        '''
