import os
from datetime import timedelta
from datetime import datetime
import base64
from time import strptime

import openpyxl
from openpyxl.utils import get_column_letter
from fast_bitrix24 import Bitrix
from time import sleep

from web_app_4dk.modules.authentication import authentication


webhook = authentication('Bitrix')
b = Bitrix(webhook)

def create_company_elapstime_report(req):

    # Формирование заголовков отчета
    report_created_time = datetime.now()
    company_id = req['company_id']

    company_info = b.get_all('crm.company.get', {'ID': company_id})
    company_name = company_info['TITLE']

    report_data = []

    total_duration = timedelta()

    # Формирование отчета

    users_info = b.get_all('user.get', {
        'filter': {
            'UF_DEPARTMENT': ['5', '231', '235'] # ЦС и ЛК
        }
    })

    users_id = list(map(lambda x: x['ID'], users_info))

    company_info = b.get_all('crm.company.get', {
        'ID': company_id,
        'select': ['TITLE'],
    })

    tasks = b.get_all('tasks.task.list', {
        'filter': {
            '>=CREATED_DATE': req['date_start'],
            'UF_CRM_TASK': ['CO_' + company_id],
        },
        'select': ['*', 'UF_CRM_TASK', 'TAGS']
    })
    tasks_id = [x['id'] for x in tasks]

    date_start = req['date_start']
    date_end = req.get('date_end')

    start_iso = f"{date_start}T00:00:00"

    if date_end:
        end_dt = datetime.strptime(date_end, "%Y-%m-%d") + timedelta(days=1)
        end_iso = end_dt.strftime("%Y-%m-%dT00:00:00")
    else:
        end_iso = datetime.now().isoformat()

    all_results = []
    page = 1

    while True:
        response = b.call(
            'task.elapseditem.getlist',
            {
                "order": {"ID": "asc"},
                "filter": {
                    "TASK_ID": tasks_id,
                    "USER_ID": users_id,
                    ">=CREATED_DATE": start_iso,
                    "<CREATED_DATE": end_iso,
                },
                "select": ["*"],
                "params": {
                    "NAV_PARAMS": {
                        "nPageSize": 50,
                        "iNumPage": page,
                    }
                },
            },
            raw=True
        )

        result = response.get("result", [])
        if not result:
            break # если страницы закончились — прерываем

        all_results.extend(result)

        page += 1 # двигаем страницу

        if page > 100: # защита от возможной бесконечной петли
            print(f"Прерывание: превышено максимальное число страниц (user_id={user_id})")
            break

        sleep(0.3)

    titles = [

        [
            company_name,
            '',
            f'{req["date_start"]} - {datetime.now()}',
        ],
        [],
        [
            'Время отнесения трудозатраты',
            'Id задачи',
            'Группа',
            'Теги ',
            'Автор трудозатраты',
            'ЧЧ:ММ:СС',
            'Комментарий',
        ]
    ]

    tasks_map = {t['id']: t for t in tasks}

    for item in all_results:

        task_id = item.get("TASK_ID")
        task_info = tasks_map.get(task_id, {})
        '''
        # группа
        group_id = str(task_info.get("group_id", ""))
        group_name = groups_map.get(group_id, "")

        # теги
        tags = task_info.get("tags", [])
        tags_str = ", ".join(tags) if tags else ""

        # пользователь
        user_id = str(item.get("USER_ID"))
        user_name = users_map.get(user_id, user_id)
        '''
        created_date = item.get("CREATED_DATE")
        seconds = int(item.get("SECONDS", 0))

        duration = timedelta(seconds=seconds)
        total_duration += duration

        # формат времени
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        duration_str = f"{hours:02}:{minutes:02}:{secs:02}"

        report_data.append([
            created_date.strftime("%d.%m.%Y"),
            task_id,
            task_info['group']['name'],
            task_info['TAGS'],
            item.get("USER_ID"),
            duration_str,
            item.get("COMMENT_TEXT", "")
        ])

    '''основная логика процесса'''


    report_data = sorted(report_data, key=lambda x: strptime(x[0], "%d.%m.%Y %H:%M:%S"))
    report_data.append(['Итого', '', '', '', '', total_duration])
    report_data = titles + report_data

    # Создание xlsx файла отчета
    report_name_time = report_created_time.strftime('%d-%m-%Y %H %M %S %f')
    report_name = f'Отчет по трудозатратам {company_name} {report_name_time}.xlsx'.replace(' ', '_')
    workbook = openpyxl.Workbook()
    worklist = workbook.active

    for data in report_data:
        worklist.append(data)
    for idx, col in enumerate(worklist.columns, 1):
        worklist.column_dimensions[get_column_letter(idx)].auto_size = True
    workbook.save(report_name)

    # Загрузка отчета в Битрикс
    bitrix_folder_id = '1947902'
    with open(report_name, 'rb') as file:
        report_file = file.read()
    report_file_base64 = str(base64.b64encode(report_file))[2:]
    upload_report = b.call('disk.folder.uploadfile', {
        'id': bitrix_folder_id,
        'data': {'NAME': report_name},
        'fileContent': report_file_base64
    })

    b.call('im.notify.system.add', {
        'USER_ID': req['user_id'][5:],
        'MESSAGE': f'Отчет по трудозатратам сформирован. {upload_report["DETAIL_URL"]}'})
    os.remove(report_name)