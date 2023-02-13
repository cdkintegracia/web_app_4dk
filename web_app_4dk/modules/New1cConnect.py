import sqlite3
import dateutil.parser
from datetime import datetime, timedelta

import requests
from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client
from zeep.transports import Transport
from fast_bitrix24 import Bitrix

try:
    from authentication import authentication
except ModuleNotFoundError:
    from web_app_4dk.modules.authentication import authentication


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


def connect_1c():
    session = Session()
    session.auth = HTTPBasicAuth('bitrix', 'SekXd4')
    client = Client('https://cus.buhphone.com/cus/ws/PartnerWebAPI2?wsdl',
                    transport=Transport(session=session))
    return client


def connect_database(table_name) -> sqlite3.Connection:
    connect = sqlite3.connect('1C_Connect.db')
    data = connect.execute(f"select count(*) from sqlite_master where type='table' and name='{table_name}'")
    for row in data:
        if row[0] == 0:
            with connect:
                connect.execute("""
                CREATE TABLE logs (
                event_type TEXT,
                event_source TEXT,
                message_type INTEGER,
                author_id TEXT,
                treatment_id TEXT,
                line_id TEXT,
                message_id TEXT,
                message_time TEXT,
                user_id TEXT,
                additional_info TEXT
                );
                """)
                connect.execute("""
                CREATE TABLE tasks (
                treatment_id TEXT,
                task_id TEXT,
                responsible_id TEXT
                );
                """)
                connect.execute("""
                CREATE TABLE companies (
                author_id TEXT,
                connect_id TEXT,
                bitrix_id TEXT,
                author_name TEXT
                );
                """)
                connect.execute("""
                CREATE TABLE users (
                connect_id TEXT,
                bitrix_id TEXT,
                name TEXT
                );
                """)
                connect.execute("""
                CREATE TABLE line_names (
                line_id TEXT,
                line_name TEXT
                );
                """)

    return connect


def send_bitrix_request(method: str, data: dict):
    return requests.post(f"{authentication('Bitrix')}{method}", json=data).json()['result']


def write_logs_to_database(log):
    additional_info = ''
    if log['message_type'] == 1:
        additional_info = log['text']
    elif log['message_type'] == 53:
        additional_info = f"Длительность: {log['rda']['duration']}"
    elif log['message_type'] == 70:
        if 'preview_link_hi' in log['file']:
            additional_info = f"{log['file']['file_name']}\n{log['file']['preview_link_hi']}\n"
        else:
            additional_info = f"{log['file']['file_name']}\n{log['file']['file_path']}\n"
    elif log['message_type'] == 82:
        additional_info = f"Длительность обращения: {log['treatment']['treatment_duration']} секунд\n"

    connect = connect_database('logs')
    sql = "INSERT INTO logs (event_type, event_source, message_type, author_id, treatment_id, line_id, message_id, message_time, user_id, additional_info) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    data = (
        log['event_type'],
        log['event_source'],
        log['message_type'],
        log['author_id'],
        log['treatment_id'],
        log['line_id'],
        log['message_id'],
        datetime.strftime(dateutil.parser.isoparse(log['message_time']) + timedelta(hours=3), '%H:%M:%S %d.%m.%Y'),
        log['user_id'],
        additional_info,
    )
    with connect:
        connect.execute(sql, data)


def write_task_id_to_database(treatment_id, task_id):
    '''
    Запись ID задачи Битрикса, созданной для указанного ID обращения. Если запись уже существует -
    обновляется значение 'treatment_id' (при переводе обращения на другую линию и др.)
    :param treatment_id: ID обращения
    :param task_id: ID задачи Битрикса
    :return:
    '''

    connect = connect_database('tasks')
    sql = 'SELECT task_id FROM tasks WHERE treatment_id=?'
    data = treatment_id
    with connect:
        is_task_exists = connect.execute(sql, data).fetchone()
    if is_task_exists:
        sql = 'UPDATE tasks SET treatment_id=? WHERE task_id=?'
    else:
        sql = 'INSERT INTO tasks (treatment_id, task_id) values (?, ?)'
    data = (
        task_id,
        treatment_id
    )
    with connect:
        connect.execute(sql, data)


def get_connect_company_id(author_id: str) -> dict:
    '''
    Получение ID компании в 1С:Коннект через выгрузку данных с портала
    :param author_id: id пользователя в 1С:Коннект
    :return:
    {'id': ..., 'inn': ..., 'author_name': ...}
    '''

    xml_client = connect_1c()

    # Получение списка сотрудников компании-клиента
    companies_employees = xml_client.service.ClientUserRead('Params')

    # Получение списка компаний-клиентов
    companies = xml_client.service.ClientRead('Params')

    # Сопоставление клиента и компании, к которой он относится
    for employee in companies_employees[1]['Value']['row']:
        if author_id == employee['Value'][0]:
            employee_company_id = employee['Value'][1]
            employee_name = f"{employee['Value'][4]} {employee['Value'][5]}"
            for company in companies[1]['Value']['row']:
                if employee_company_id == company['Value'][0]:
                    connect_company_id = company['Value'][0]
                    if company['Value'][4]:
                        company_inn = company['Value'][4].strip()
                        return {'id': connect_company_id, 'inn': company_inn, 'author_name': employee_name}


def get_bitrix_company_id(author_id: str) -> str:
    '''
    Получение ID компании в Битриксе из БД. Если запись не найдена - происходит попытка создания новой.
    В случае неудачи - создается задача в Битриксе, информирующая об этом.
    :param author_id: id пользователя из 1С:Коннект
    :return:
    company['ID']
    '''

    connect = connect_database('companies')
    sql = 'SELECT bitrix_id FROM companies WHERE author_id=?'
    data = (
        author_id,
    )
    with connect:
        bitrix_company_id = connect.execute(sql, data).fetchone()
    if bitrix_company_id:
        return bitrix_company_id[0]
    else:
        connect_company_info = get_connect_company_id(author_id)
        print('ghbsdfdsgsd', connect_company_info)
        if connect_company_info:
            bitrix_company_info = b.get_all(
                'crm.company.list',
                {'select': ['ID'],
                 'filter': {
                     'UF_CRM_1656070716': connect_company_info['inn']
                 }})
            if bitrix_company_info:
                bitrix_company_id = bitrix_company_info[0]['ID']
                sql = 'INSERT INTO companies (author_id, connect_id, bitrix_id) values (?, ?, ?)'
                data = (
                    author_id,
                    connect_company_info['id'],
                    bitrix_company_id,
                )
                with connect:
                    connect.execute(sql, data)
                return bitrix_company_id
            else:
                send_bitrix_request('tasks.task.add', {
                            'fields': {
                                'TITLE': '1С:Коннект Не найдена компания по ИНН',
                                'DESCRIPTION': f"ИНН: {connect_company_info['inn']}\n",
                                'CREATED_BY': '173',
                                'RESPONSIBLE_ID': '173',
                                'GROUP_ID': '75',
                                'STAGE_ID': '0',
                            }})


def get_bitrix_user_name(connect_user_id: str) -> str:
    '''
    Получение имени фамилии и имени сотрудника из БД. Если запись не найдена - происходит попытка создания новой
    :param connect_user_id: id пользователя из 1С:Коннект
    :return:
    {Фамилия} {Имя}
    '''

    connect = connect_database('users')
    sql = 'SELECT name FROM users WHERE connect_id=?'
    data = (
        connect_user_id,
    )
    with connect:
        user_name = connect.execute(sql, data).fetchone()
    if user_name:
        return user_name[0]
    else:
        xml_client = connect_1c()
        connect_users_info = xml_client.service.SpecialistRead('Params')
        for connect_user in connect_users_info[1]['Value']['row']:
            connect_user_id = connect_user['Value'][0]
            connect_first_name = connect_user['Value'][3]
            connect_last_name = connect_user['Value'][4]
            req_data = {
                'filter': {
                    'NAME': connect_first_name,
                    'LAST_NAME': connect_last_name,
                }
            }
            bitrix_user_info = requests.post(url=f"{authentication('Bitrix')}user.get", json=req_data).json()['result']
            bitrix_user_info = bitrix_user_info[0]
            if bitrix_user_info:
                sql = 'INSERT INTO users (connect_id, bitrix_id, name) VALUES (?, ?, ?)'
                data = (
                    connect_user_id,
                    bitrix_user_info['ID'],
                    f"{connect_first_name} {connect_last_name}"
                )
                with connect:
                    connect.execute(sql, data)
                return f"{connect_first_name} {connect_last_name}"


def get_line_name(line_id: str) -> str:
    connect = connect_database('line_names')
    sql = 'SELECT line_name FROM line_names WHERE line_id=?'
    data = (
        line_id,
    )
    with connect:
        line_name = connect.execute(sql, data).fetchone()
        if line_name:
            return line_name[0]
        else:
            xml_client = connect_1c()
            lines = xml_client.service.ServiceLineKindRead('Params')[1]['Value']['row']
            for line in lines:
                if line['Value'][0] == line_id:
                    line_name = line['Value'][2]
                    sql = 'INSERT INTO line_names (line_name, line_id) VALUES (?, ?)'
                    data = (
                        line_name,
                        line_id,
                    )
                    with connect:
                        connect.execute(sql, data)
                    return line_name


def create_treatment_task(treatment_id: str, author_id: str, line_id: str):
    connect = connect_database('tasks')

    '''
    Проверка была ли уже создана задача
    '''

    sql = 'SELECT task_id FROM tasks WHERE treatment_id=?'
    data = (
        treatment_id,
    )
    with connect:
        task_id = connect.execute(sql, data).fetchone()
    if task_id:
        return

    '''
    Создание задачи
    '''

    company_id = get_bitrix_company_id(author_id)

    if not company_id:
        return

    sql = 'SELECT author_name FROM companies WHERE author_id=?'
    data = (
        author_id,
    )
    with connect:
        author_name = connect.execute(sql, data).fetchone()[0]

    sql = 'SELECT additional_info, message_time, line_id FROM logs WHERE treatment_id=? and message_type!=80'
    data = (
        treatment_id,
    )
    with connect:
        row = connect.execute(sql, data).fetchone()
    additional_info = row[0]

    # Проверка на наличие хотя бы одного русского символа в сообщении
    russian_char_flag = False
    for word in additional_info:
        for char in word:
            if 1040 <= ord(char) <= 1103:
                russian_char_flag = True
    if russian_char_flag is False:
        return

    # Проверка сообщения через фильтр
    filter_word_list = [
        'спасибо',
    ]
    if additional_info.lower().strip('!-_/|\\+,.? ') in filter_word_list:
        return

    message_time = row[1]
    line_name = get_line_name(line_id)
    task_description = f"{message_time} {author_name}\n{additional_info}"
    responsible_id = '311'
    if 'ЛК' in line_name:
        new_task = send_bitrix_request('tasks.task.add', {'fields': {
            'TITLE': f"1С:Коннект {line_name}",
            'DESCRIPTION': f"{task_description}",
            #'GROUP_ID': '7',
            'GROUP_ID': '19',
            'CREATED_BY': '173',
            'RESPONSIBLE_ID': responsible_id,
            'UF_CRM_TASK': [f"CO_{company_id}"],
            'STAGE_ID': '65',
            'UF_AUTO_499889542776': treatment_id
        }})
    elif 'Обновить 1С' in line_name:
        new_task = send_bitrix_request('tasks.task.add', {'fields': {
            'TITLE': f"1С:Коннект ТЛП",
            'DESCRIPTION': f"{task_description}",
            #'GROUP_ID': '11',
            'GROUP_ID': '19',
            'CREATED_BY': '173',
            'RESPONSIBLE_ID': responsible_id,
            'UF_CRM_TASK': [f"CO_{company_id}"],
            'UF_AUTO_499889542776': treatment_id
        }})
    else:
        new_task = send_bitrix_request('tasks.task.add', {'fields': {
            'TITLE': f"1С:Коннект {line_name}",
            'DESCRIPTION': f"{task_description}",
            'GROUP_ID': '19',
            'CREATED_BY': '173',
            'RESPONSIBLE_ID': responsible_id,
            'UF_CRM_TASK': [f"CO_{company_id}"],
            'STAGE_ID': '1165',
            'UF_AUTO_499889542776': treatment_id
        }})
    new_task_id = new_task['task']
    connect = connect_database('tasks')
    sql = 'INSERT INTO tasks (treatment_id, task_id, responsible_id) VALUES (?, ?, ?)'
    data = (
        treatment_id,
        new_task_id['id'],
        responsible_id,
    )
    with connect:
        connect.execute(sql, data)


def create_logs_commentary(treatment_id: str) -> str:
    connect = connect_database('logs')
    sql = 'SELECT author_id, message_type, additional_info, message_time FROM logs WHERE treatment_id=? and message_type!=80'
    data = (
        treatment_id,
    )
    with connect:
        logs = connect.execute(sql, data).fetchall()[1:]
    sql = 'SELECT task_id FROM tasks WHERE treatment_id=?'
    with connect:
        task_id = connect.execute(sql, data).fetchone()[0]
    task_comments = requests.get(f'{authentication("Bitrix")}task.commentitem.getlist?ID={task_id}').json()[
        'result']
    commentary = ''
    for comment in task_comments:
        if 'История обращения 1С:Коннект' not in comment['POST_MESSAGE']:
            continue
        send_bitrix_request('task.commentitem.delete', {0: task_id, 1: comment['ID']})
        commentary = comment['POST_MESSAGE']
    if not commentary:
        commentary = 'История обращения 1С:Коннект\n' + '-' * 40 + '\n\n'

    for log in logs:

        # ID пользователя в имя
        user_name = ''
        sql = 'SELECT author_name FROM companies WHERE author_id=?'
        data = (
            log[0],
        )
        with connect:
            result = connect.execute(sql,data).fetchone()
        if result:
            user_name = result[0]
        if not user_name:
            sql = 'SELECT name FROM users WHERE connect_id=?'
            with connect:
                result = connect.execute(sql, data).fetchone()
            if result:
                user_name = result[0]

        commentary += f'{log[3]}\n{user_name}\n{connect_codes[log[1]]}\n{log[2]}\n\n'
    return commentary


def close_treatment_task(treatment_id: str, treatment_duration: int):
    connect = connect_database('tasks')
    sql = 'SELECT task_id FROM tasks WHERE treatment_id=?'
    data = (
        treatment_id,
    )
    with connect:
        task_id = connect.execute(sql, data).fetchone()
    if not task_id:
        return

    task_id = task_id[0]
    commentary = create_logs_commentary(treatment_id)
    b.call('task.commentitem.add', [task_id, {'POST_MESSAGE': commentary, 'AUTHOR_ID': '173'}],
           raw=True)
    send_bitrix_request('tasks.task.update', {'taskId': task_id, 'fields': {'STATUS': '5'}})
    elapsed_time = treatment_duration
    b.call('task.elapseditem.add', [task_id, {'SECONDS': elapsed_time, 'USER_ID': '173'}], raw=True)


def complete_database_update():
    '''
    Полное обновление БД (таблицы 'companies' и 'users')
    '''

    bitrix_companies = b.get_all('crm.company.list', {'select': ['UF_CRM_1656070716']})
    xml_client = connect_1c()

    # Обновление таблицы companies
    connect = connect_database('companies')
    companies_employees = xml_client.service.ClientUserRead('Params')
    companies = xml_client.service.ClientRead('Params')
    for employee in companies_employees[1]['Value']['row']:
        employee_name = f"{employee['Value'][4]} {employee['Value'][5]}"
        employee_id = employee['Value'][0]
        sql = 'SELECT author_id FROM companies WHERE author_id=?'
        data = (
            employee_id,
        )
        with connect:
            row = connect.execute(sql, data).fetchone()
        if not row:
            employee_company_id = employee['Value'][1]
            for company in companies[1]['Value']['row']:
                if employee_company_id == company['Value'][0]:
                    connect_company_id = company['Value'][0]
                    if company['Value'][4]:
                        company_inn = company['Value'][4].strip()
                        bitrix_id = list(filter(lambda x: x['UF_CRM_1656070716'] == company_inn, bitrix_companies))
                        if bitrix_id:
                            bitrix_id = bitrix_id[0]['ID']
                            sql = 'INSERT INTO companies (author_id, connect_id, bitrix_id, author_name) values (?, ?, ?, ?)'
                            data = (
                                employee_id,
                                connect_company_id,
                                bitrix_id,
                                employee_name
                            )
                            with connect:
                                connect.execute(sql, data)

    # Обновление таблицы users
    bitrix_users_info = b.get_all('user.get')
    connect = connect_database('users')
    connect_users_info = xml_client.service.SpecialistRead('Params')
    for connect_user in connect_users_info[1]['Value']['row']:
        connect_user_id = connect_user['Value'][0]
        connect_user_name = f"{connect_user['Value'][3]} {connect_user['Value'][4]}"
        bitrix_user = list(filter(lambda x: connect_user_name == f"{x['NAME']} {x['LAST_NAME']}", bitrix_users_info))
        if bitrix_user:
            bitrix_user = bitrix_user[0]
            bitrix_user_id = bitrix_user['ID']
            sql = 'INSERT INTO users (connect_id, bitrix_id, name) VALUES (?, ?, ?)'
            data = (
                connect_user_id,
                bitrix_user_id,
                connect_user_name
            )
            with connect:
                connect.execute(sql, data)

    # Обновление таблицы line_names
    lines = xml_client.service.ServiceLineKindRead('Params')[1]['Value']['row']
    for line in lines:
        line_id = line['Value'][0]
        sql = 'SELECT line_name FROM line_names WHERE line_id=?'
        data = (
            line_id,
        )
        with connect:
            line_name = connect.execute(sql, data).fetchone()
        if not line_name:
            line_name = line['Value'][2]
            sql = 'INSERT INTO line_names (line_name, line_id) VALUES (?, ?)'
            data = (
                line_name,
                line_id,
            )
            with connect:
                connect.execute(sql, data)


def connect_1c_event_handler(req):
    if req['event_type'] != 'line':
        return
    write_logs_to_database(req)

    # Новое обращение
    if req['message_type'] == 80:
        create_treatment_task(req['treatment_id'], req['user_id'], req['line_id'])

    # Завершение обращения
    elif req['message_type'] in [82, 90, 91, 92, 93]:
        print(req)
        close_treatment_task(req['treatment_id'], req['treatment']['treatment_duration'])

    # Перевод обращения на другую линию
    elif req['message_type'] == 89 and req['data']['direction'] == 'to':
        connect = connect_database('tasks')
        sql = 'SELECT task_id FROM tasks WHERE treatment_id=?'
        data = (
            req['treatment_id'],
        )
        with connect:
            task_id = connect.execute(sql, data).fetchone()
        if not task_id:
            return
        task_id = task_id[0]
        line_name = get_line_name(req['line_id'])

        if 'ЛК' in line_name:
            send_bitrix_request('tasks.task.update', {
                'taskId': task_id,
                'fields': {
                    'GROUP_ID': '7',
                    'STAGE_ID': '65',
                    'UF_AUTO_499889542776': req['data']['treatment_id']
                }})
        elif 'Обновить 1С' in line_name:
            send_bitrix_request('tasks.task.update', {
                'taskId': task_id,
                'fields': {
                    'GROUP_ID': '11',
                    'UF_AUTO_499889542776': req['data']['treatment_id']
                }})
        commentary = create_logs_commentary(req['treatment_id'])
        b.call('task.commentitem.add', [task_id, {'POST_MESSAGE': commentary, 'AUTHOR_ID': '173'}],
               raw=True)

        sql = 'UPDATE tasks SET treatment_id=? WHERE task_id=?'
        data = (
            req['data']['treatment_id'],
            task_id,
        )
        with connect:
            connect.execute(sql, data)

        # Ответственный за задачу != сотрудник поддержки
        connect = connect_database('users')
        sql = 'SELECT bitrix_id FROM users WHERE connect_id=?'
        data = (
            req['user_id'],
        )
        with connect:
            user_bitrix_id = connect.execute(sql, data).fetchone()
        if not user_bitrix_id:
            return
        user_bitrix_id = user_bitrix_id[0]
        sql = 'SELECT responsible_id FROM tasks WHERE treatment_id=?'
        data = (
            req['treatment_id'],
        )
        with connect:
            responsible_id = connect.execute(sql, data).fetchone()[0]
        if responsible_id != user_bitrix_id:
            send_bitrix_request('tasks.task.update', {'fields': {'RESPONSIBLE_ID': user_bitrix_id, 'AUDITORS': []}})







