from datetime import datetime, timedelta
import requests
from fast_bitrix24 import Bitrix
from web_app_4dk.modules.authentication import authentication

b = Bitrix(authentication('Bitrix'))

GROUP_ID = '7' # id группы ЛК
EXCEPT_USER_ID = '173' # id Робота Задач


def get_fio_from_user_info(user_info: dict) -> str:
    """
    Возвращает Фамилию Имя пользователя
    """

    return (
        f'{user_info.get("LAST_NAME", "")} '
        f'{user_info.get("NAME", "")}'
    ).strip()


def seconds_to_hms(seconds: int) -> str:
    """
    Перевод секунд в HH:MM:SS
    """

    return str(timedelta(seconds=seconds))


def closed_lk_tasks(req=None):

    now = datetime.now()

    day_title = now.strftime('%d.%m.%Y')

    start_day = now.strftime('%Y-%m-%d') + 'T00:00:00+03:00'
    end_day = now.strftime('%Y-%m-%d') + 'T23:59:59+03:00'


    # всего создано задач за сегодня
    created_tasks = b.get_all(
        'tasks.task.list',
        {
            'filter': {
                'GROUP_ID': GROUP_ID,
                '>=CREATED_DATE': start_day,
                '<=CREATED_DATE': end_day
            },
            'select': ['ID']
        }
    )
    total_created = len(created_tasks)

    # всего закрыто задач за сегодня
    closed_tasks = b.get_all(
        'tasks.task.list',
        {
            'filter': {
                'GROUP_ID': GROUP_ID,
                'REAL_STATUS': '5',
                '>=CLOSED_DATE': start_day,
                '<=CLOSED_DATE': end_day,
            },
            'select': [
                'ID',
                'RESPONSIBLE_ID',
                'CLOSED_DATE',
                'UF_AUTO_499889542776'
            ]
        }
    )
    total_closed = len(closed_tasks)

    # список id закрытых задач коннекта
    connect_tasks = [task for task in closed_tasks if task.get('ufAuto499889542776')]
    connect_task_ids  = [task['id'] for task in connect_tasks]

    # все трудозатраты из закрытых задач коннекта
    elapsed_items = []

    if connect_task_ids :

        page = 1
        page_size = 50

        while True:

            response = b.call(
                'task.elapseditem.getlist',
                {
                    "order": {"ID": "asc"},
                    "filter": {
                        "TASK_ID": connect_task_ids 
                    },
                    "select": ["*"],
                    "params": {
                        "NAV_PARAMS": {
                            "nPageSize": page_size,
                            "iNumPage": page,
                        }
                    },
                },
                raw=True
            )

            result = response.get("result", [])

            if not result:
                break

            elapsed_items.extend(result)

            page += 1


    # статистика по сотрудникам
    user_stat = {}
    total_seconds = 0

    # считаем задачи по каждому сотруднику
    for task in closed_tasks:

        user_id = str(task['responsibleId'])

        if user_id == EXCEPT_USER_ID:
            continue

        if user_id not in user_stat:
            user_stat[user_id] = {
                'count': 0,
                'connect_seconds': 0,
                'call_seconds': 0
            }

        user_stat[user_id]['count'] += 1
    
    user_ids_lk = list(user_stat.keys()) # список сотрудников для выборки звонков

    # считаем звонки
    calls = b.get_all(
        'voximplant.statistic.get',
        {
            'filter': {
                'CALL_TYPE': 1,
                'PORTAL_USER_ID': user_ids_lk,
                '>=CALL_START_DATE': start_day,
                '<=CALL_START_DATE': end_day,
                'CALL_FAILED_CODE': '200',
            }
        }
    )

    for call in calls:

        user_id = str(call['PORTAL_USER_ID'])

        if user_id not in user_stat:
            continue

        user_stat[user_id]['call_seconds'] += int(
            call.get('CALL_DURATION', 0)
        )

    # считаем трудозатраты по каждому сотруднику
    for item in elapsed_items:

        user_id = str(item['USER_ID'])

        if user_id == EXCEPT_USER_ID:
            continue

        if user_id not in user_stat:
            continue

        user_stat[user_id]['connect_seconds'] += int(item['SECONDS'])

    total_seconds = sum(stat['connect_seconds'] + stat['call_seconds'] for stat in user_stat.values())


    # получам ФИ сотрудников
    users = b.get_all(
        'user.get',
        {
            'filter': {
                'ID': list(user_stat.keys())
            }
        }
    )

    users_map = {}

    for user in users:
        users_map[user['ID']] = get_fio_from_user_info(user)


    # собираем отчет
    total_spent_time = seconds_to_hms(total_seconds)

    report = (
        f'[b]Отчет по задачам за {day_title} '
        f'(Кол-во / Время)[/b]\n\n'
    )

    report += f'Всего поступило: {total_created}\n'
    report += (
        f'Всего завершено: '
        f'{total_closed} ({total_spent_time})\n\n'
    )

    report += '[b]Статистика по исполнителям:[/b]\n\n'

    sorted_users = sorted(
        user_stat.items(),
        key=lambda x: x[1]['count'],
        reverse=True
    )

    for user_id, stat in sorted_users:

        user_name = users_map.get(
            user_id,
            f'Пользователь {user_id}' # если у сотрудника полностью нет ФИ, что в целом невозможно
        )

        spent_time = seconds_to_hms(stat['connect_seconds'] + stat['call_seconds'])

        report += (
            f'{user_name} '
            f'{stat["count"]} '
            f'({spent_time})\n'
        )

    #print(report)


    # отправка отчета

    notification_users = ['1391']
    #notification_users = ['159', '1391']

    for user in notification_users:

        data = {
            'DIALOG_ID': user,
            'MESSAGE': report,
        }

        requests.post(
            url=f'{authentication("user_173").strip()}im.message.add',
            json=data
        )


if __name__ == '__main__':
    closed_lk_tasks()