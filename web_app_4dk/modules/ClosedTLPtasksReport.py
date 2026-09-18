from datetime import datetime, timedelta
import requests
from fast_bitrix24 import Bitrix
if __package__:
    # Импорт при работе внутри приложения на сервере.
    from .authentication import authentication
else:
    # Прямой запуск файла локально.
    from authentication import authentication

b = Bitrix(authentication('Bitrix'))

GROUP_ID = '1' # id группы ТЛП
PAID_GROUP_ID = '408' # id группы платных работ
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


def build_group_report(group_id, title, start_day, end_day):
    """Время за все даты по закрытым сегодня задачам выбранной группы.

    Сохранено правило: время учитывается только для сотрудников,
    у которых есть закрытая сегодня задача в этой же группе.
    Пользователь 173 исключается из статистики сотрудников, но его
    задачи остаются в общем количестве поступивших и завершённых.
    """
    # всего создано задач за сегодня
    created_tasks = b.get_all(
        'tasks.task.list',
        {
            'filter': {
                'GROUP_ID': group_id,
                '>=CREATED_DATE': start_day,
                '<=CREATED_DATE': end_day,
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
                'GROUP_ID': group_id,
                'REAL_STATUS': '5',
                '>=CLOSED_DATE': start_day,
                '<=CLOSED_DATE': end_day,
            },
            'select': [
                'ID',
                'RESPONSIBLE_ID',
                'CLOSED_DATE'
            ]
        }
    )
    total_closed = len(closed_tasks)

    # список id закрытых задач
    closed_task_ids = [task['id'] for task in closed_tasks]


    # все трудозатраты из закрытых задач
    elapsed_items = []

    if closed_task_ids:

        page = 1
        page_size = 50

        while True:

            response = b.call(
                'task.elapseditem.getlist',
                {
                    "order": {"ID": "asc"},
                    "filter": {
                        "TASK_ID": closed_task_ids
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
                'seconds': 0
            }

        user_stat[user_id]['count'] += 1

    # считаем трудозатраты по каждому сотруднику
    for item in elapsed_items:

        user_id = str(item['USER_ID'])

        if user_id == EXCEPT_USER_ID:
            continue

        if user_id not in user_stat:
            continue

        seconds = int(item['SECONDS'])

        user_stat[user_id]['seconds'] += seconds

        total_seconds += seconds


    # получам ФИ сотрудников
    users = b.get_all(
        'user.get',
        {
            'filter': {
                'ID': list(user_stat.keys())
            }
        }
    ) if user_stat else []

    users_map = {}

    for user in users:
        users_map[str(user['ID'])] = get_fio_from_user_info(user)


    # собираем отчет
    total_spent_time = seconds_to_hms(total_seconds)

    report = f'[b]{title}[/b]\n\n'

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

        spent_time = seconds_to_hms(stat['seconds'])

        report += (
            f'{user_name} '
            f'{stat["count"]} '
            f'({spent_time})\n'
        )

    return report.rstrip()


def closed_tlp_tasks(req=None):
    now = datetime.now()
    day_title = now.strftime('%d.%m.%Y')
    start_day = now.strftime('%Y-%m-%d') + 'T00:00:00+03:00'
    end_day = now.strftime('%Y-%m-%d') + 'T23:59:59+03:00'

    blocks = [
        build_group_report(GROUP_ID, 'ТЛП', start_day, end_day),
        build_group_report(PAID_GROUP_ID, 'Платные работы', start_day, end_day),
    ]
    report = (
        f'[b]Отчет по задачам за {day_title} '
        f'(Кол-во / Время)[/b]\n\n'
        + '\n\n'.join(blocks)
    )

    # Единое сообщение пользователю 159 и в чат chat21.
    for dialog_id in ('159', 'chat21'):
    #for dialog_id in ('1'):
        requests.post(
            url=f'{authentication("user_173").strip()}im.message.add',
            json={'DIALOG_ID': dialog_id, 'MESSAGE': report},
        )


if __name__ == '__main__':
    closed_tlp_tasks()
