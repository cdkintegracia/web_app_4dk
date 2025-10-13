from datetime import datetime, timedelta
from time import sleep
import base64
import requests
from fast_bitrix24 import Bitrix
from web_app_4dk.modules.authentication import authentication

b = Bitrix(authentication('Bitrix'))

def get_employee_id(users: str) -> list:
    """
    Приводит строку с id пользователей и id подразделений к единому списку, состоящему только из id сотрудников

    :param users: Строка из параметра запроса Б24 состоящая из {user_...} и|или {group_...}, которые разделены ', '
    """

    users_id_set = set()

    # Строка с сотрудниками и отделами в список
    users = users.split(', ')

    # Если в массиве найден id сотрудника
    for user_id in users:
        if 'user' in user_id:
            users_id_set.add(user_id[5:])

        # Если в массиве найден id отдела
        elif 'group' in user_id:
            department_users = b.get_all('user.get', {'filter': {'UF_DEPARTMENT': user_id[8:]}})
            for user in department_users:
                users_id_set.add(user['ID'])

    return list(users_id_set)

def get_fio_from_user_info(user_info: dict) -> str:
    """
    Возвращает строку, состоящую из фамилии и имени пользователя Б24

    :param user_info: Словарь, полученный запросом с методом user.get
    """

    return (f'{user_info["NAME"] if "NAME" in user_info else ""}'
            f' {user_info["LAST_NAME"] if "LAST_NAME" in user_info else ""}').strip()

def test_employee_activity_report(req):

    report_day = datetime.now()
    day_title = datetime.strftime(report_day, '%d.%m.%y')
    report_day = datetime.strftime(report_day, '%Y-%m-%d') + 'T00:00:00+03:00'

    users_id = ['153'] # по кому формируем отчет ('1435' - ШАА, '6605' - БЕВ)
    #users_id = get_employee_id(req['users'])
    users_info = b.get_all('user.get', {
        'filter': {
            'ACTIVE': 'true',
            'ID': users_id,
        }
    })

    for user_info in users_info:

        user_name = get_fio_from_user_info(user_info)
        text_message = f'[b]Отчет по активности {user_name} за {day_title}[/b]\n\n'

        # сбор инфо по исходящим более 10 секунд за день
        calls = b.get_all('voximplant.statistic.get', {
            'filter': {
                'CALL_TYPE': 1,
                'PORTAL_USER_ID': user_info['ID'],
                '>CALL_DURATION': 10,
                '>=CALL_START_DATE': report_day,
                'CALL_FAILED_CODE': '200',
            }})
        text_message += f'Исходящих звонков свыше 10 сек.: {len(calls)}\n'
        
        #сбор инфо по исходящим письмам с привязкой к сущностям
        emails = b.get_all('crm.activity.list', {
            'filter': {
                'PROVIDER_TYPE_ID': 'EMAIL',
                'AUTHOR_ID': user_info['ID'],
                '>=CREATED': report_day,
                'DIRECTION': '2'
                }})
        text_message += f'Отправлено писем: {len(emails)}\n'

        sleep(1)

        #сбор инфо по кол-ву закрытых задач с тегом презентация
        presentation = b.get_all('tasks.task.list', {
            'filter': {
                '%TAG': 'презентация',
                'RESPONSIBLE_ID': user_info['ID'],
                '>=CLOSED_DATE': report_day
                }})
        text_message += f'Проведено презентаций: {len(presentation)}\n'

        #сбор инфо по трудозатратам внесенным сегодня
        '''
        time_spent = b.get_all('tasks.task.list', {
            'filter': {
                'RESPONSIBLE_ID': user_info['ID'],
                '>=CLOSED_DATE': report_day
                }})

        time_spent = int(sum(list(map(lambda x: int(x['timeSpentInLogs']), time_spent))) / 60)
        '''
        time_spent = b.call('task.elapseditem.getlist', {
            'order': {
                'ID': 'asc'
                },
            'filter': {
                'USER_ID': user_info['ID'],
                '>=CREATED_DATE': report_day}
            }, raw=True)['result']
        time_spent = sum(list(map(lambda x: int(x['MINUTES']), time_spent)))
        text_message += f'Трудозатрат по задачам: {time_spent} минут\n'

        #сбор инфо по выставленным счетам сегодня
        account_sp = b.get_all('crm.item.list', {
            'entityTypeId': 1082,
            'filter': {
                'ASSIGNED_BY_ID': user_info['ID'],
                '>=UF_CRM_77_1759836894': report_day
                }})
        account = len(account_sp)

        if user_info['ID'] == '1435': #если отчет по ШАА
            account_st = b.get_all('crm.item.list', {
                'entityTypeId': 31,
                'filter': {
                    'ASSIGNED_BY_ID': user_info['ID'],
                    '>=BEGINDATE': report_day
                    }})
            account += len(account_st)

        text_message += f'Выставлено счетов: {account}\n'

        #print(text_message)

        #рассылка от робота задач
        notification_users = ['1391']
        #notification_users = [user_info['ID'], '1', '1391']
        #notification_users = ['chat25605']
        for user in notification_users:
            data = {
                'DIALOG_ID': user,
                'MESSAGE': text_message,
            }

            r = requests.post(url=f'{authentication("user_173").strip()}im.message.add', json=data)
        '''
        #рассылка от службы качества чдк для СНА 157
        data = {
            'DIALOG_ID': '157',
            'MESSAGE': text_message,
        }
        r = requests.post(url=f'{authentication("user_639").strip()}im.message.add', json=data)
        '''
if __name__ == '__main__':
    test_employee_activity_report()