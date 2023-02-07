import sqlite3
import dateutil.parser
from datetime import datetime

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
                if table_name == 'logs':
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
                elif table_name == 'tasks':
                    connect.execute("""
                    CREATE TABLE tasks (
                    treatment_id TEXT,
                    task_id TEXT
                    );
                    """)
                elif table_name == 'companies':
                    connect.execute("""
                    CREATE TABLE companies (
                    author_id TEXT,
                    connect_id TEXT,
                    bitrix_id TEXT,
                    author_name TEXT
                    );
                    """)
                elif table_name == 'users':
                    connect.execute("""
                    CREATE TABLE companies (
                    connect_id TEXT,
                    name TEXT
                    );
                    """)

    return connect


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
        datetime.strftime(dateutil.parser.isoparse(log['message_time']), '%Y.%m.%d %H:%M:%S'),
        log['user_id'],
        additional_info,
    )
    with connect:
        connect.execute(sql, data)


def write_task_id_to_database(treatment_id, task_id):
    connect = connect_database('tasks')
    sql = 'SELECT task_id FROM tasks WHERE treatment_id=?'
    data = treatment_id
    with connect:
        is_task_exists = connect.execute(sql, data).fetchone()
    if is_task_exists:
        sql = 'UPDATE tasks SET task_id=? WHERE treatment_id=?'
    else:
        sql = 'INSERT INTO tasks (treatment_id, task_id) values (?, ?)'
    data = (
        task_id,
        treatment_id
    )
    with connect:
        connect.execute(sql, data)


def get_connect_company_id(author_id):
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
                    company_inn = company['Value'][4].strip()
                    return {'id': connect_company_id, 'inn': company_inn, 'author_name': employee_name}


def get_bitrix_company_id(author_id):
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
                b.call('tasks.task.add', {
                            'fields': {
                                'TITLE': '1С:Коннект Не найдена компания по ИНН',
                                'DESCRIPTION': f"ИНН: {connect_company_info['inn']}\n",
                                'CREATED_BY': '173',
                                'RESPONSIBLE_ID': '173',
                                'GROUP_ID': '75',
                                'STAGE_ID': '0',
                            }})


def get_bitrix_user_name(connect_user_id):
    pass



#print(get_bitrix_company_id('2a7d1ebd-c1df-45f7-933f-6f2263491b47'))

