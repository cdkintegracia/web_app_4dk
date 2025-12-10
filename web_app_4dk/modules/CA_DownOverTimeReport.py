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

    return (f'{user_info["LAST_NAME"] if "LAST_NAME" in user_info else ""}'
            f' {user_info["NAME"] if "NAME" in user_info else ""}'
            f' {user_info["SECOND_NAME"] if "SECOND_NAME" in user_info else ""}').strip()

def ca_downovertime_report(req):

    users_id = get_employee_id(req['users'])
    users_info = b.get_all('user.get', {
        'filter': {
            'ACTIVE': 'true',
            'ID': users_id,
        }
    })


    report_day = datetime.today()
    year, week, weekday = report_day.isocalendar()
    start_week = datetime.fromisocalendar(year, week, 1) - timedelta(days=7)
    end_week = start_week + timedelta(days=6)
    start_month = report_day.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    print(start_week)
    print(end_week)
    print(start_month)


    #собираем общие данные по рабочим часам за неделю и месяц
    week_calendar = b.get_all('crm.item.list', { #смарт-процесс Производственный календарь
        'entityTypeId': '1098',
        'filter': {
            'categoryId': 115,
            '>=ufCrm85_Day': start_week,
            '<=ufCrm85_Day': end_week
            }})
    week_calendar = sum(list(map(lambda x: int(x['ufCrm85_Hours']), week_calendar)))
    print(week_calendar)

    month_calendar = b.get_all('crm.item.list', { #смарт-процесс Производственный календарь
        'entityTypeId': '1098',
        'filter': {
            'categoryId': 115,
            '>=ufCrm85_Day': start_month,
            '<=ufCrm85_Day': end_week
            }})
    month_calendar = sum(list(map(lambda x: int(x['ufCrm85_Hours']), month_calendar)))
    print(month_calendar)


    for user_info in users_info:

        user_name = get_fio_from_user_info(user_info)
        text_message = f'[b]{user_name}[/b]\n\n'

        

        print(text_message)
        '''
        sleep(1)

        #сбор инфо по кол-ву закрытых задач с тегом презентация
        presentation = b.get_all('tasks.task.list', {
            'filter': {
                '%TAG': 'презентация',
                'RESPONSIBLE_ID': user_info['ID'],
                '>=CLOSED_DATE': report_day
                }})
        text_message += f'Проведено презентаций: {len(presentation)}\n'

        #сбор инфо по трудозатратам внесенным сегодня - архив
        
        time_spent = b.get_all('tasks.task.list', {
            'filter': {
                'RESPONSIBLE_ID': user_info['ID'],
                '>=CLOSED_DATE': report_day
                }})

        time_spent = int(sum(list(map(lambda x: int(x['timeSpentInLogs']), time_spent))) / 60)
        
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
        account_sp = b.get_all('crm.item.list', { #смарт-процесс Выставленные счета (выгружаются из СОУ)
            'entityTypeId': '1082',
            'filter': {
                'assignedById': user_info['ID'],
                '>=ufCrm77_1759836894': report_day
                }})
        account = len(account_sp)

        
        text_message += f'Выставлено счетов: {account}\n'

        #print(text_message)

        #рассылка от робота задач
        notification_users = ['1391']
        #notification_users = [user_info['ID'], '1', '1391']

        for user in notification_users:
            data = {
                'DIALOG_ID': user,
                'MESSAGE': text_message,
            }

            r = requests.post(url=f'{authentication("user_173").strip()}im.message.add', json=data)
        
        #рассылка от службы качества чдк для СНА 157
        data = {
            'DIALOG_ID': '1391',
            'MESSAGE': text_message,
        }
        r = requests.post(url=f'{authentication("user_639").strip()}im.message.add', json=data)
        '''
if __name__ == '__main__':
    ca_downovertime_report()