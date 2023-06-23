from datetime import datetime, timedelta
import base64
import os

from fast_bitrix24 import Bitrix
import openpyxl

try:
    from authentication import authentication
except ModuleNotFoundError:
    from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))

groups_info = {
    'ТЛП': {'group_id': '1', 'stage_id': '15'},
    'ЛК': {}
}


def get_tasks(group_name, start_date_filter, end_date_filter):
    tasks = b.get_all('tasks.task.list', {
        'select': ['*', 'UF_*'],
        'filter': {
            'GROUP_ID': groups_info[group_name]['group_id'],
            'STAGE_ID': groups_info[group_name]['stage_id'],
            '>=CLOSED_DATE': start_date_filter,
            '<CLOSED_DATE': end_date_filter,
        }
    })
    return tasks


def create_satisfaction_assessment_report(req):
    start_date_filter = datetime.strptime(req['start_date_filter'], '%d.%m.%Y')
    end_date_filter = (datetime.strptime(req['end_date_filter'], '%d.%m.%Y'))
    tasks = get_tasks(req['group_name'], start_date_filter.strftime('%Y-%m-%d'), (end_date_filter + timedelta(days=1)).strftime('%Y-%m-%d'))
    excel_data = [
        [req['group_name'], f'с {req["start_date_filter"]} по {req["end_date_filter"]}', f'Дата формирования {datetime.now().strftime("%d.%m.%Y %H:%M")}'],
        ['', ]
    ]

    # Создание строки с датами
    date_data = ['', ]
    count_date = start_date_filter
    while count_date != end_date_filter + timedelta(days=1):
        date_data.append(count_date)
        count_date = count_date + timedelta(days=1)
    else:
        excel_data.append(date_data)

    # Подсчет задач для каждой даты
    all_tasks = ['Всего завершено', ]
    no_answer_tasks = ['Без ответов', ]
    tasks_with_rating = {
        '5': ['5', ],
        '4': ['4', ],
        '3': ['3', ],
        '2': ['2', ],
        '1': ['1', ],
    }
    for d in date_data:
        if d:
            filter_date = d.strftime('%d.%m.%Y')
            date_all_tasks = list(filter(lambda x: (datetime.fromisoformat(x['createdDate'])).strftime('%d.%m.%Y') == filter_date, tasks))
            all_tasks.append(len(date_all_tasks))
            date_no_answer_tasks = list(filter(lambda x: x['ufAuto475539459870'] and not x['ufAuto177856763915'], date_all_tasks))
            no_answer_tasks.append(len(date_no_answer_tasks))

            for rating in tasks_with_rating.keys():
                rating_tasks = list(filter(lambda x: rating == x['ufAuto177856763915'], date_all_tasks))
                tasks_with_rating[rating].append(len(rating_tasks))

    excel_data.append(all_tasks)
    excel_data.append(no_answer_tasks)
    for rating, data in tasks_with_rating.items():
        excel_data.append(data)

    excel_data.append(['', ])
    excel_data.append(['Оценки ниже 5'])
    low_rating_tasks = list(filter(lambda x: x['ufAuto177856763915'] and int(x['ufAuto177856763915']) < 5, tasks))
    if low_rating_tasks:
        low_rating_tasks = list(sorted(low_rating_tasks, key=lambda x: int(x['ufAuto177856763915'])))
        for task in low_rating_tasks:
            uf_crm_company = list(filter(lambda x: 'CO_' in x, task['ufCrmTask']))
            if uf_crm_company:
                company_id = uf_crm_company[0][3:]
                company_info = b.get_all('crm.company.get', {
                    'ID': company_id,
                })
                company_title = company_info['TITLE']
            else:
                company_title = ''
            excel_data.append([
                task['ufAuto177856763915'],
                company_title,
                f'https://vc4dk.bitrix24.ru/workgroups/group/{groups_info[req["group_name"]]["group_id"]}/tasks/task/view/{task["id"]}/'
            ])

    # Создание xlsx файла
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    for index, row in enumerate(excel_data):

        # Преобразование строки с датами из datetime в str
        if index == 2:
            new_row_date = []
            for cell in row:
                if cell:
                    new_row_date.append(cell.strftime('%d.%m.%Y'))
                else:
                    new_row_date.append('')
            worksheet.append(new_row_date)
        else:
            worksheet.append(row)
    report_name = f'Отчет_по_оценкам_клиентов_{datetime.now().strftime("%d_%m_%Y_%H_%M_%S")}.xlsx'
    workbook.save(report_name)

    # Загрузка отчета в Битрикс
    bitrix_folder_id = '495759'
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
        'MESSAGE': f'Отчет по сумме сервисов сформирован. {upload_report["DETAIL_URL"]}'})
    os.remove(report_name)
