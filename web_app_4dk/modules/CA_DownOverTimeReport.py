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

def get_time_spent_for_period(b, user_id, start_iso, end_iso):
    """
    Возвращает список трудозатрат за период [start_iso, end_iso),
    автоматически дробит период на 3 части при >50 записей
    """

    # первый запрос — проверочный
    result = b.call('task.elapseditem.getlist', {
        'order': {'ID': 'asc'},
        'filter': {
            'USER_ID': user_id,
            '>=CREATED_DATE': start_iso,
            '<CREATED_DATE': end_iso
        },
        'select': ['*']
    }, raw=True)['result']

    if len(result) <= 49:
        return result

    # если записей много — дробим период на 3 части
    start_dt = datetime.fromisoformat(start_iso)
    end_dt = datetime.fromisoformat(end_iso)
    start_day = start_dt.date()
    end_day = end_dt.date()

    total_days = (end_day - start_day).days
    if total_days < 1:
        total_days = 1

    segment_days = total_days // 3
    remainder = total_days % 3

    segments = []
    current_start = start_day

    for i in range(3):
        extra_day = 1 if i < remainder else 0
        seg_end = current_start + timedelta(days=segment_days + extra_day)

        seg_start_str = datetime.combine(current_start, start_dt.time()).isoformat()
        seg_end_str = datetime.combine(seg_end, start_dt.time()).isoformat()

        segments.append((seg_start_str, seg_end_str))
        current_start = seg_end

    all_results = []
    for seg_start, seg_end in segments:
        part = b.call('task.elapseditem.getlist', {
            'order': {'ID': 'asc'},
            'filter': {
                'USER_ID': user_id,
                '>=CREATED_DATE': seg_start,
                '<CREATED_DATE': seg_end
            },
            'select': ['*']
        }, raw=True)['result']

        all_results.extend(part)

    return all_results


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
    end_week = start_week + timedelta(days=7)
    start_month = start_week.replace(day=1)
    if start_week.month == 12:
        end_month = start_week.replace(year=start_week.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end_month = start_week.replace(month=start_week.month + 1, day=1) - timedelta(days=1)

    if start_month.month == end_week.month:
        last_day_month = end_week
    else:
        last_day_month = end_month

    #start_week = datetime.strftime(start_week, '%Y-%m-%d') + 'T00:00:00+03:00'
    #end_week = datetime.strftime(end_week, '%Y-%m-%d') + 'T00:00:00+03:00'
    #start_month = datetime.strftime(start_month, '%Y-%m-%d') + 'T00:00:00+03:00'
    #end_month = datetime.strftime(end_month, '%Y-%m-%d') + 'T00:00:00+03:00'
    #last_day_month = datetime.strftime(last_day_month, '%Y-%m-%d') + 'T00:00:00+03:00'
    start_week = '2025-11-24T00:00:00+03:00'
    end_week = '2025-12-01T00:00:00+03:00'
    start_month = '2025-11-01T00:00:00+03:00'
    end_month = '2025-11-30T00:00:00+03:00'
    last_day_month = '2025-11-30T00:00:00+03:00'

    print(start_week)
    print(end_week)
    print(start_month)
    print(end_month)
    print(last_day_month)


    #собираем общие данные по рабочим часам за неделю и месяц
    week_calendar = b.get_all('crm.item.list', { #смарт-процесс Производственный календарь
        'entityTypeId': '1098',
        'select': ['ufCrm85_Hours'],
        'filter': {
            'categoryId': 115,
            '>=ufCrm85_Day': start_week,
            '<ufCrm85_Day': end_week
            }})
    week_calendar = sum(list(map(lambda x: int(x['ufCrm85_Hours']), week_calendar)))
    print(week_calendar)

    month_calendar = b.get_all('crm.item.list', { #смарт-процесс Производственный календарь
        'entityTypeId': '1098',
        'select': ['ufCrm85_Hours'],
        'filter': {
            'categoryId': 115,
            '>=ufCrm85_Day': start_month,
            '<ufCrm85_Day': last_day_month
            }})
    month_calendar = sum(list(map(lambda x: int(x['ufCrm85_Hours']), month_calendar)))
    print(month_calendar)


    for user_info in users_info:

        # получаем имя сотрудника
        user_name = get_fio_from_user_info(user_info)
        text_message = f'[b]{user_name}[/b]\n\n'


        #собираем персональные данные по рабочим часам за неделю и месяц
        week_absent = b.get_all('crm.item.list', { #смарт-процесс Отсутствия за неделю
            'entityTypeId': '1102',
            'select': ['ufCrm87_Hours'],
            'filter': {
                'categoryId': 119,
                'ufCrm87_Person': user_info['ID'],
                '>=ufCrm87_Day': start_week,
                '<ufCrm87_Day': end_week
                }})
        week_absent = sum(list(map(lambda x: int(x['ufCrm87_Hours']), week_absent)))
        print(week_absent)

        month_absent = b.get_all('crm.item.list', { #смарт-процесс Отсутствия за месяц
            'entityTypeId': '1102',
            'select': ['ufCrm87_Hours'],
            'filter': {
                'categoryId': 119,
                'ufCrm87_Person': user_info['ID'],
                '>=ufCrm87_Day': start_month,
                '<ufCrm87_Day': last_day_month
                }})
        month_absent = sum(list(map(lambda x: int(x['ufCrm87_Hours']), month_absent)))
        print(month_absent)


        total_hours_week = week_calendar - week_absent # всего рабочих часов за неделю
        total_hours_month = month_calendar - month_absent # всего рабочих часов за месяц


        # делаем запрос трудозатрат за неделю
        time_spent_week_list = get_time_spent_for_period(
            b=b,
            user_id=user_info['ID'],
            start_iso=start_week,
            end_iso=end_week
        )
        time_spent_week = sum(int(x['MINUTES']) for x in time_spent_week_list)

        print('Записей за неделю:', len(time_spent_week_list))
        print('Минут за неделю:', time_spent_week)

        # собираем словарь, где по каждому task_id сумма трудозатрат за неделю
        task_week = {}
        for item in time_spent_week_list:
            task_id = item.get('TASK_ID')
            minutes = int(item.get('MINUTES', 0))

            if task_id in task_week:
                task_week[task_id] += minutes
            else:
                task_week[task_id] = minutes

        # запрашиваем по получившимся task_id названия задач
        task_ids_week = list(task_week.keys())
        tasks = b.get_all('tasks.task.list', {
            'filter': {
                'ID': task_ids_week
            },
            'select': ['ID', 'TITLE']
        })

        # собираем строки, где по каждому task_id есть название и сумма трудозатрат в часах
        task_titles = {}
        for task in tasks:
            task_titles[int(task['id'])] = task['title']

        time_spent_week = []
        for task_id, minutes in task_week.items():
            title = task_titles[int(task_id)]
            hours = round(minutes / 60, 2)  # Переводим минуты в часы и округляем до 2 знаков
            time_spent_week.append(f'({task_id}) {title}: {hours} ч')
        
        month_1 = datetime.fromisoformat(start_week).strftime("%d.%m.%y")
        month_2 = datetime.fromisoformat(end_week).strftime("%d.%m.%y")

        text_message += f'[i]1. За период с {month_1} по {month_2} Вами отработаны задачи:[/i]\n'
        for task_id in time_spent_week:
            text_message += f'{task_id}\n'

        hours_week = round(sum(task_week.values()) / 60, 2)
        text_message += f'[i][b]Итого отработано:[/b][/i] {hours_week} ч\n'

        downovertime_week = total_hours_week - hours_week
        if downovertime_week >= 0:
            text_message += f'[i][b]Простой:[/b][/i] {abs(downovertime_week)} ч'
        else: text_message += f'[i][b]Переработка:[/b][/i] {abs(downovertime_week)} ч'
        
                
        # делаем запрос трудозатрат за месяц
        time_spent_month_list = get_time_spent_for_period(
            b=b,
            user_id=user_info['ID'],
            start_iso=start_month,
            end_iso=last_day_month
        )
        time_spent_month = sum(int(x['MINUTES']) for x in time_spent_month_list)

        print('Записей за месяц:', len(time_spent_month_list))
        print('Минут за месяц:', time_spent_month)

        # собираем словарь, где по каждому task_id сумма трудозатрат за месяц
        task_month = {}
        for item in time_spent_month_list:
            task_id = item.get('TASK_ID')
            minutes = int(item.get('MINUTES', 0))

            if task_id in task_month:
                task_month[task_id] += minutes
            else:
                task_month[task_id] = minutes

        # запрашиваем по получившимся task_id названия задач
        task_ids_month = list(task_month.keys())
        tasks = b.get_all('tasks.task.list', {
            'filter': {
                'ID': task_ids_month
            },
            'select': ['ID', 'TITLE']
        })

        # собираем строки, где по каждому task_id есть название и сумма трудозатрат в часах
        task_titles = {}
        for task in tasks:
            task_titles[int(task['id'])] = task['title']

        time_spent_month = []
        for task_id, minutes in task_month.items():
            title = task_titles[int(task_id)]
            hours = round(minutes / 60, 2)  # Переводим минуты в часы и округляем до 2 знаков
            time_spent_month.append(f'({task_id}) {title}: {hours} ч')
        
        month_1 = datetime.fromisoformat(start_month).strftime("%d.%m.%y")
        month_2 = datetime.fromisoformat(last_day_month).strftime("%d.%m.%y")

        text_message += f'\n\n[i]2. За период с {month_1} по {month_2} Вами отработаны задачи:[/i]\n'
        for task_id in time_spent_month:
            text_message += f'{task_id}\n'

        hours_month = round(sum(task_month.values()) / 60, 2)
        text_message += f'[i][b]Итого отработано:[/b][/i] {hours_month} ч\n'

        downovertime_month = total_hours_month - hours_month
        if downovertime_month >= 0:
            text_message += f'[i][b]Простой:[/b][/i] {abs(downovertime_month)} ч'
        else: text_message += f'[i][b]Переработка:[/b][/i] {abs(downovertime_month)} ч'

        print(text_message)

        #рассылка от робота задач
        notification_users = ['1391']
        #notification_users = [user_info['ID'], '1', '1391']

        for user in notification_users:
            data = {
                'DIALOG_ID': user,
                'MESSAGE': text_message,
            }

            r = requests.post(url=f'{authentication("user_173").strip()}im.message.add', json=data)

        sleep(1)

        '''
        #рассылка от службы качества чдк для СНА 157
        data = {
            'DIALOG_ID': '1391',
            'MESSAGE': text_message,
        }
        r = requests.post(url=f'{authentication("user_639").strip()}im.message.add', json=data)
    
        '''

if __name__ == '__main__':

    ca_downovertime_report()