from datetime import datetime
import base64
import os

import openpyxl
from openpyxl.styles import PatternFill, Font
from openpyxl.utils import get_column_letter

from fast_bitrix24 import Bitrix
from authentication import authentication

b = Bitrix(authentication('Bitrix'))


def normalize_number(value):
    """
    Нормализация номера реализации
    """

    if not value:
        return ''

    return str(value).strip().replace(' ', '')


def change_sheet_style(sheet):

    for column_cells in sheet.columns:

        length = max(
            len(str(cell.value) if cell.value else '')
            for cell in column_cells
        )

        sheet.column_dimensions[
            get_column_letter(column_cells[0].column)
        ].width = min(length * 1.2, 60)


def report_paid_tasks(req):

    date_from = req['date_from']
    date_to = req['date_to']

    # =========================================================
    # ПОЛУЧАЕМ ЭЛЕМЕНТЫ СОУ
    # =========================================================

    debts = b.get_all(
        'crm.item.list',
        {
            'entityTypeId': 161,
            'select': [
                'id',
                'ufCrm41_Provider',
                'ufCrm41_1689101328',
                'UF_CRM_41_1689101306',
                'ufCrm41_1690546413',
                'ufCrm41_1689101272'
            ],
            'filter': {
                '>=ufCrm41_1689101272': date_from,
                '<=ufCrm41_1689101272': date_to,
                '!ufCrm41_1733668627': '1'
            }
        }
    )

    # =========================================================
    # ПОЛУЧАЕМ ЗАДАЧИ ПУ
    # =========================================================

    tasks = b.get_all(
        'tasks.task.list',
        {
            'filter': {
                'GROUP_ID': 408,
                '>=CREATED_DATE': date_from,
                '<=CREATED_DATE': date_to
            },
            'select': [
                'ID',
                'TITLE',
                'RESPONSIBLE_ID',
                'CREATED_DATE',
                'UF_AUTO_210185778353',
                'UF_AUTO_324696461819',
                'UF_CRM_TASK'
            ]
        }
    )

    # =========================================================
    # СОБИРАЕМ ID ПОЛЬЗОВАТЕЛЕЙ И КОМПАНИЙ
    # =========================================================

    user_ids = set()
    company_ids = set()

    # СОУ

    for debt in debts:

        provider = debt.get('ufCrm41_Provider')

        if provider:
            user_ids.add(str(int(float(provider))))

        company = debt.get('ufCrm41_1690546413')

        if company:
            company_ids.add(str(company))

    # ЗАДАЧИ

    for task in tasks:

        responsible_id = task.get('responsibleId')

        if responsible_id:
            user_ids.add(str(responsible_id))

        crm_links = task.get('ufCrmTask', [])

        if crm_links:

            for link in crm_links:

                if str(link).startswith('CO_'):

                    company_id = str(link).replace('CO_', '')
                    company_ids.add(company_id)

    # =========================================================
    # ПОЛЬЗОВАТЕЛИ
    # =========================================================

    users = {}

    if user_ids:

        users_data = b.get_all(
            'user.get',
            {
                'ID': list(user_ids)
            }
        )

        for user in users_data:

            users[str(user['ID'])] = (
                f"{user['NAME']} {user['LAST_NAME']}"
            )

    # =========================================================
    # КОМПАНИИ
    # =========================================================

    companies = {}

    if company_ids:

        companies_data = b.get_all(
            'crm.company.list',
            {
                'filter': {
                    'ID': list(company_ids)
                },
                'select': [
                    'ID',
                    'TITLE'
                ]
            }
        )

        for company in companies_data:

            companies[str(company['ID'])] = company['TITLE']

    # =========================================================
    # СОУ
    # =========================================================

    debts_dict = {}

    for debt in debts:

        number = normalize_number(
            debt.get('UF_CRM_41_1689101306')
        )

        if not number:
            continue

        act_date = debt.get('ufCrm41_1689101272')

        year = datetime.fromisoformat(
            act_date
        ).year

        key = (year, number)

        provider = debt.get('ufCrm41_Provider')

        provider_name = ''

        if provider:
            provider_name = users.get(
                str(int(float(provider))),
                ''
            )

        company_id = debt.get('ufCrm41_1690546413')

        debts_dict[key] = {
            'id': debt.get('id'),
            'number': number,
            'executor': provider_name,
            'company': companies.get(str(company_id), ''),
            'amount': debt.get('ufCrm41_1689101328'),
            'date': act_date
        }

    # =========================================================
    # ЗАДАЧИ
    # =========================================================

    tasks_dict = {}

    tasks_without_number = []

    for task in tasks:

        number = normalize_number(
            task.get('ufAuto324696461819')
        )

        created_date = task.get('createdDate')

        year = datetime.fromisoformat(
            created_date
        ).year

        responsible_name = users.get(
            str(task.get('responsibleId')),
            ''
        )

        # Компания

        task_company = ''

        crm_links = task.get('ufCrmTask', [])

        if crm_links:

            for link in crm_links:

                if str(link).startswith('CO_'):

                    company_id = str(link).replace('CO_', '')

                    task_company = companies.get(
                        company_id,
                        ''
                    )

                    break

        task_data = {
            'id': task.get('id'),
            'number': number,
            'executor': responsible_name,
            'company': task_company,
            'amount': task.get('ufAuto210185778353'),
            'date': created_date
        }

        # Задачи без номера

        if not number:

            tasks_without_number.append(task_data)
            continue

        key = (year, number)

        tasks_dict[key] = task_data

    # =========================================================
    # СОБИРАЕМ ВСЕ КЛЮЧИ
    # =========================================================

    all_keys = set(
        debts_dict.keys()
    ) | set(
        tasks_dict.keys()
    )

    # =========================================================
    # EXCEL
    # =========================================================

    workbook = openpyxl.Workbook()

    ws = workbook.active
    ws.title = 'Сверка'

    headers = [
        'Статус',

        'Номер реализации',

        'ID задачи',
        'ID элемента СОУ',

        'Исполнитель задача',
        'Исполнитель СОУ',

        'Компания задача',
        'Компания СОУ',

        'Сумма задача',
        'Сумма СОУ',

        'Дата задачи',
        'Дата акта'
    ]

    ws.append(headers)

    # =========================================================
    # СТИЛИ
    # =========================================================

    header_fill = PatternFill(
        start_color='D9EAD3',
        end_color='D9EAD3',
        fill_type='solid'
    )

    green_fill = PatternFill(
        start_color='C6EFCE',
        end_color='C6EFCE',
        fill_type='solid'
    )

    yellow_fill = PatternFill(
        start_color='FFF2CC',
        end_color='FFF2CC',
        fill_type='solid'
    )

    red_fill = PatternFill(
        start_color='F4CCCC',
        end_color='F4CCCC',
        fill_type='solid'
    )

    for cell in ws[1]:

        cell.font = Font(bold=True)
        cell.fill = header_fill

    # =========================================================
    # ЗАПОЛНЕНИЕ
    # =========================================================

    for key in sorted(all_keys):

        debt = debts_dict.get(key)
        task = tasks_dict.get(key)

        # =======================================
        # СТАТУС
        # =======================================

        if debt and task:

            status = 'Совпало'

            if (
                str(debt.get('executor')) != str(task.get('executor'))
                or
                str(debt.get('company')) != str(task.get('company'))
                or
                str(debt.get('amount')) != str(task.get('amount'))
            ):
                status = 'Расхождение'

        elif debt and not task:

            status = 'Нет в ПУ'

        elif task and not debt:

            status = 'Нет в СОУ'

        else:
            status = ''

        # =======================================
        # СТРОКА
        # =======================================

        row = [
            status,

            debt.get('number') if debt else task.get('number'),

            task.get('id') if task else '',
            debt.get('id') if debt else '',

            task.get('executor') if task else '',
            debt.get('executor') if debt else '',

            task.get('company') if task else '',
            debt.get('company') if debt else '',

            task.get('amount') if task else '',
            debt.get('amount') if debt else '',

            task.get('date') if task else '',
            debt.get('date') if debt else ''
        ]

        ws.append(row)

        current_row = ws.max_row

        # =======================================
        # ЦВЕТА СТРОК
        # =======================================

        if status == 'Совпало':

            fill = green_fill

        elif status == 'Расхождение':

            fill = yellow_fill

        else:

            fill = red_fill

        for cell in ws[current_row]:

            cell.fill = fill

    # =========================================================
    # ОТСТУП
    # =========================================================

    ws.append([])
    ws.append([])
    ws.append([])

    # =========================================================
    # ЗАГОЛОВОК БЛОКА
    # =========================================================

    title_row = ws.max_row + 1

    ws.cell(
        row=title_row,
        column=1,
        value='Задачи без номера реализации'
    )

    ws.cell(
        row=title_row,
        column=1
    ).font = Font(
        bold=True,
        size=14
    )

    # =========================================================
    # ЗАГОЛОВКИ
    # =========================================================

    headers_row = ws.max_row + 1

    headers_without_number = [
        'ID задачи',
        'Исполнитель',
        'Компания',
        'Сумма',
        'Дата задачи'
    ]

    for col_num, header in enumerate(headers_without_number, 1):

        cell = ws.cell(
            row=headers_row,
            column=col_num,
            value=header
        )

        cell.font = Font(bold=True)
        cell.fill = header_fill

    # =========================================================
    # ДАННЫЕ
    # =========================================================

    for task in tasks_without_number:

        ws.append([
            task['id'],
            task['executor'],
            task['company'],
            task['amount'],
            task['date']
        ])


    change_sheet_style(ws)

    report_name = f'Отчет_по_платным_задачам_{datetime.now().strftime("%d_%m_%Y_%H_%M_%S")}.xlsx'
    workbook.save(report_name)

    # Загрузка отчета в Битрикс
    bitrix_folder_id = '2041440'
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
        'MESSAGE': f'Отчет по платным задачам сформирован. {upload_report["DETAIL_URL"]}'})
    os.remove(report_name)


if __name__ == '__main__':

    report_paid_tasks({
        'date_from': '2026-01-01',
        'date_to': '2026-12-31',
        'user_id': 'user_1391'
    })