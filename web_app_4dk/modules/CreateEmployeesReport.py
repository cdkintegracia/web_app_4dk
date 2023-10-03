from datetime import datetime, timedelta
from calendar import monthrange
import base64
import os

import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.styles import PatternFill, Font
from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))
deals_info_files_directory = f'/root/web_app_4dk/web_app_4dk/modules/deals_info_files/'
#deals_info_files_directory = f'C:\\Users\\Максим\\Documents\\GitHub\\web_app_4dk\\web_app_4dk\\deals_info_files\\'
month_int_names = {
        1: 'Январь',
        2: 'Февраль',
        3: 'Март',
        4: 'Апрель',
        5: 'Май',
        6: 'Июнь',
        7: 'Июль',
        8: 'Август',
        9: 'Сентябрь',
        10: 'Октябрь',
        11: 'Ноябрь',
        12: 'Декабрь',
    }


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

    '''
    return f'{user_info["LAST_NAME"] if "LAST_NAME" in user_info else ""}'\
           f' {user_info["NAME"] if "NAME" in user_info else ""}'.strip()
    '''

    return (f'{user_info["NAME"] if "NAME" in user_info else ""}'
            f' {user_info["LAST_NAME"] if "LAST_NAME" in user_info else ""}').strip()


def change_sheet_style(sheet) -> None:

    # Изменение ширины
    for column_cells in sheet.columns:
        length = max(len(str(cell.value) if cell.value else '') for cell in column_cells)
        sheet.column_dimensions[get_column_letter(column_cells[0].column)].width = length * 1.1


def get_quarter_filter(month_number):
    quarters = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
        [10, 11, 12]
    ]
    quarter = list(filter(lambda x: month_number in x, quarters))[0]
    if month_number + 1 in quarter:
        quarter.remove(month_number + 1)
    quarter_start_filter = datetime(day=1, month=quarter[0], year=datetime.now().year)
    quarter_end_filter = datetime(day=1, month=quarter[-1] + 1, year=datetime.now().year)

    return {
        'start_date': quarter_start_filter,
        'end_date': quarter_end_filter
    }


def read_deals_data_file(month, year):
    filename = f'{month_int_names[month]}_{year}.xlsx'
    workbook = openpyxl.load_workbook(f'{deals_info_files_directory}{filename}')
    worksheet = workbook.active
    file_titles = ['Предполагаемая дата закрытия', 'Дата начала', 'Ответственный', 'Тип', 'Сумма', 'Стадия сделки',
                   'Группа', 'ID', 'Название сделки']
    file_data = []
    for row in worksheet.rows:
        row_data = list(map(lambda x: x.value, row))
        row_data = dict(zip(file_titles, row_data))
        file_data.append(row_data)
    return file_data


def create_employees_report(req):
    users_id = get_employee_id(req['users'])
    users_info = b.get_all('user.get', {
        'filter': {
            'ACTIVE': 'true',
            'ID': users_id,
        }
    })

    deal_fields = b.get_all('crm.deal.fields')

    report_year = datetime.now().year
    report_month = datetime.now().month - 1
    if report_month == 0:
        report_month = 12
        report_year -= 1
    report_month_range = monthrange(report_year, report_month)[1]
    report_month_last_day_date = (f'{report_month_range}.'
                                  f'{report_month if len(str(report_month)) == 2 else "0" + str(report_month)}.'
                                  f'{report_year}')
    before_last_month = report_month - 1
    before_last_month_year = report_year
    if before_last_month == 0:
        before_last_month = 12
        before_last_month_year -= 1

    month_filter_start = datetime(day=1, month=report_month, year=report_year)
    month_filter_end = datetime(day=1, month=datetime.now().month, year=datetime.now().year)
    ddmmyyyy_pattern = '%d.%m.%Y'
    quarter_filters = get_quarter_filter(datetime.now().month - 1)

    workbook = openpyxl.Workbook()
    report_name = f'Отчет_по_сотрудникам_{datetime.now().strftime("%d_%m_%Y_%H_%M_%S")}.xlsx'
    month_names = {
        1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август', 9: 'Сентябрь',
        10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
    }

    deal_group_field = deal_fields['UF_CRM_1657878818384']['items']
    deal_group_field.append({'ID': None, 'VALUE': 'Остальные'})

    for index, user_info in enumerate(users_info):
        user_name = get_fio_from_user_info(user_info)
        if index == 0:
            worksheet = workbook.active
            worksheet.title = user_name
        else:
            worksheet = workbook.create_sheet(user_name)

        worksheet.append([user_name, '', f'{month_names[report_month]} {report_year}'])
        worksheet.append([])
        worksheet.append([])

        # Отчетность
        # Отчетный месяц
        last_month_deals_data = read_deals_data_file(report_month, report_year)
        free_reporting_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and
                                                      x['Тип'] == 'Отчетность (в рамках ИТС)',
                                                      last_month_deals_data))

        prof_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and
                                                      x['Группа'] == 'ИТС' and
                                                      'Базовый' not in x['Тип'], last_month_deals_data))

        its_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and
                                                     x['Группа'] == 'ИТС', last_month_deals_data))

        try:
            coverage_free_reporting_deals_last_month = round(len(free_reporting_deals_last_month) /
                                                             len(prof_deals_last_month), 2) * 100
        except ZeroDivisionError:
            coverage_free_reporting_deals_last_month = 0

        paid_reporting_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and
                                                                x['Тип'] == 'Отчетность', last_month_deals_data))

        try:
            coverage_paid_reporting_deals_last_month = round(round(len(paid_reporting_deals_last_month) /
                                                             len(its_deals_last_month), 2) * 100, 2)
        except ZeroDivisionError:
            coverage_paid_reporting_deals_last_month = 0

        # Предшествующий отчетному месяц
        before_last_month_deals_data = read_deals_data_file(before_last_month, before_last_month_year)

        free_reporting_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and
                                                      x['Тип'] == 'Отчетность (в рамках ИТС)', before_last_month_deals_data))

        prof_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and
                                                   x['Группа'] == 'ИТС' and
                                                   'Базовый' not in x['Тип'], before_last_month_deals_data))

        its_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and
                                                  x['Группа'] == 'ИТС', before_last_month_deals_data))

        try:
            coverage_free_reporting_deals_before_last_month = round(round(len(free_reporting_deals_before_last_month) /
                                                                    len(prof_deals_before_last_month), 2) * 100, 2)
        except ZeroDivisionError:
            coverage_free_reporting_deals_before_last_month = 0

        paid_reporting_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and
                                                             x['Тип'] == 'Отчетность', before_last_month_deals_data))

        try:
            coverage_paid_reporting_deals_before_last_month = round(round(len(paid_reporting_deals_before_last_month) /
                                                                    len(its_deals_before_last_month), 2) * 100, 2)
        except ZeroDivisionError:
            coverage_paid_reporting_deals_before_last_month = 0

        # Начало года
        start_year_deals_data = read_deals_data_file(1, report_year)
        free_reporting_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and
                                                      x['Тип'] == 'Отчетность (в рамках ИТС)',
                                                      start_year_deals_data))

        prof_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and
                                            x['Группа'] == 'ИТС' and
                                            'Базовый' not in x['Тип'], start_year_deals_data))

        its_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and
                                           x['Группа'] == 'ИТС', start_year_deals_data))

        try:
            coverage_free_reporting_deals_start_year = round(round(len(free_reporting_deals_start_year) /
                                                             len(prof_deals_start_year), 2) * 100, 2)
        except ZeroDivisionError:
            coverage_free_reporting_deals_start_year = 0

        paid_reporting_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and
                                                      x['Тип'] == 'Отчетность',
                                                      start_year_deals_data))

        try:
            coverage_paid_reporting_deals_start_year = round(round(len(paid_reporting_deals_start_year) /
                                                             len(its_deals_start_year), 2) * 100, 2)
        except ZeroDivisionError:
            coverage_paid_reporting_deals_start_year = 0



        worksheet.append(['Отчетность', f'на {report_month_last_day_date}', 'Прирост за месяц', 'Прирост с начала года',
                          'На начало года'])
        worksheet.append([
            'Льготных отчетностей',
            len(free_reporting_deals_last_month),
            len(free_reporting_deals_last_month) - len(free_reporting_deals_before_last_month),
            len(free_reporting_deals_last_month) - len(free_reporting_deals_start_year),
            len(free_reporting_deals_start_year),
        ])
        worksheet.append([
            'Охват льготной отчетностью',
            f'{coverage_free_reporting_deals_last_month}%',
            f'{coverage_free_reporting_deals_last_month - coverage_free_reporting_deals_before_last_month}%',
            f'{coverage_free_reporting_deals_last_month - coverage_free_reporting_deals_start_year}%',
            f'{coverage_free_reporting_deals_start_year}%',
        ])
        worksheet.append([
            'Платных отчетностей',
            len(paid_reporting_deals_last_month),
            len(paid_reporting_deals_last_month) - len(paid_reporting_deals_before_last_month),
            len(paid_reporting_deals_last_month) - len(paid_reporting_deals_start_year),
            len(paid_reporting_deals_start_year),
        ])
        worksheet.append([
            'Охват платных отчетностей',
            f'{coverage_paid_reporting_deals_last_month}%',
            f'{coverage_paid_reporting_deals_last_month - coverage_paid_reporting_deals_before_last_month}%',
            f'{coverage_paid_reporting_deals_last_month - coverage_paid_reporting_deals_start_year}%',
            f'{coverage_paid_reporting_deals_start_year}%',
        ])
        worksheet.append([])

        # Продажи
        sales = b.get_all('crm.item.list', {
            'entityTypeId': '133',
            'filter': {
                'assignedById': user_info['ID'],
                '>=ufCrm3_1654248264': month_filter_start.strftime(ddmmyyyy_pattern),
                '<ufCrm3_1654248264': month_filter_end.strftime(ddmmyyyy_pattern),
            }
        })

        sold_deals = b.get_all('crm.deal.list', {
            'select': ['UF_CRM_1657878818384', 'OPPORTUNITY'],
            'filter': {
                'ID': list(map(lambda x: x['parentId2'], sales))
            }
        })

        worksheet.append(['Продажи', f'{month_names[report_month]} {report_year} шт.', f'{month_names[report_month]} {report_year} руб'])
        for field_value in deal_group_field:
            grouped_deals = list(filter(lambda x: x['UF_CRM_1657878818384'] == field_value['ID'], sold_deals))
            worksheet.append([field_value['VALUE'], len(grouped_deals), sum(list(map(lambda x: float(x['OPPORTUNITY']), grouped_deals)))])
        worksheet.append(['Всего по источникам', len(sales), sum(list(map(lambda x: x['opportunity'], sales)))])
        worksheet.append(['Всего по сделкам', len(sold_deals), sum(list(map(lambda x: float(x['OPPORTUNITY']), sold_deals)))])
        worksheet.append([])


        # Долги по документам
        documents_debts = b.get_all('crm.item.list', {
            'entityTypeId': '161',
            'filter': {
                'assignedById': user_info['ID'],
                'stageId': 'DT161_53:NEW',
                '<ufCrm41_1689101272': quarter_filters['end_date'].strftime(ddmmyyyy_pattern)
            }
        })
        quarter_documents_debts = list(filter(lambda x:
                                              quarter_filters['start_date'].timestamp() <=
                                              datetime.fromisoformat(x['ufCrm41_1689101272']).timestamp()
                                              < quarter_filters['end_date'].timestamp(), documents_debts))

        non_quarter_documents_debts = len(documents_debts) - len(quarter_documents_debts)

        worksheet.append(['Долги по документам', 'За текущий квартал', 'За предыдущие периоды'])
        worksheet.append(['Штук', len(quarter_documents_debts), non_quarter_documents_debts])
        worksheet.append([])

        # Задачи
        tasks = b.get_all('tasks.task.list', {
            'filter': {
                'RESPONSIBLE_ID': user_info['ID'],
                '>=CREATED_DATE': month_filter_start.strftime(ddmmyyyy_pattern),
                '<CREATED_DATE': month_filter_end.strftime(ddmmyyyy_pattern),
            },
            'select': ['GROUP_ID', 'STATUS', 'UF_AUTO_177856763915']
        })
        completed_tasks = list(filter(lambda x: x['status'] == '5', tasks))
        service_tasks = list(filter(lambda x: x['groupId'] == '71', tasks))
        completed_service_tasks = list(filter(lambda x: x['status'] == '5', service_tasks))
        completed_other_tasks = list(filter(lambda x: x['status'] == '5' and x['groupId'] != '71', tasks))
        non_completed_other_tasks = list(filter(lambda x: x['status'] != '5' and x['groupId'] != '71', tasks))
        completed_tlp_tasks = list(filter(lambda x: x['groupId'] == '1' and x['status'] == '5', tasks))
        tasks_ratings = list(map(lambda x: int(x['ufAuto177856763915']) if x['ufAuto177856763915'] else 0, completed_tlp_tasks))
        tasks_ratings = list(filter(lambda x: x != 0, tasks_ratings))
        try:
            average_tasks_ratings = round(sum(tasks_ratings) / len(tasks_ratings), 2)
        except ZeroDivisionError:
            average_tasks_ratings = '-'

        worksheet.append(['', 'Незакрытых (и созд. в этом мес)', 'Всего создано в месяце'])
        worksheet.append(['Незакрытые задачи', len(tasks) - len(completed_tasks), len(tasks)])
        worksheet.append(['СВ', len(service_tasks) - len(completed_service_tasks), len(service_tasks)])
        worksheet.append(['Остальные', len(non_completed_other_tasks), len(completed_other_tasks) + len(non_completed_other_tasks)])
        worksheet.append([])
        worksheet.append(['Закрытые задачи ТЛП', len(completed_tlp_tasks)])
        worksheet.append(['Средняя оценка', average_tasks_ratings])

        change_sheet_style(worksheet)

    workbook.save(report_name)

    if 'user_id' not in req:
        return

    # Загрузка отчета в Битрикс
    bitrix_folder_id = '600147'
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
        'MESSAGE': f'Отчет по активностям сформирован. {upload_report["DETAIL_URL"]}'})
    os.remove(report_name)


if __name__ == '__main__':
    create_employees_report({
        'users': 'user_355'  #'user_129'   #'group_dr27', 'user_135'
    })




