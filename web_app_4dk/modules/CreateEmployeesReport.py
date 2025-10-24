from datetime import datetime, timedelta
from calendar import monthrange
import base64
import os

import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.styles import PatternFill, Font
from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication
from web_app_4dk.modules.EdoInfoHandler import month_codes, year_codes
from web_app_4dk.modules.field_values import month_int_names


b = Bitrix(authentication('Bitrix'))
deals_info_files_directory = f'/root/web_app_4dk/web_app_4dk/modules/deals_info_files/'
#deals_info_files_directory = f'C:\\Users\\Максим\\Documents\\GitHub\\web_app_4dk\\web_app_4dk\\deals_info_files\\'


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
    #добавлено 01 01 2024
    if month_number == 12:
        quarter_start_filter = datetime(day=1, month=quarter[0], year=datetime.now().year-1)
    else:
        quarter_start_filter = datetime(day=1, month=quarter[0], year=datetime.now().year)

    month_end = quarter[-1] + 1
    year_end=datetime.now().year
    if month_end == 13:
        month_end = 1
        #ibs 2025-01-11
        #year_end = year_end + 1
    quarter_end_filter = datetime(day=1, month=month_end, year=year_end)

    return {
        'start_date': quarter_start_filter,
        'end_date': quarter_end_filter
    }


def read_deals_data_file(month, year):
    filename = f'{month_int_names[month]}_{year}.xlsx'
    workbook = openpyxl.load_workbook(f'{deals_info_files_directory}{filename}')
    worksheet = workbook.active
    file_data = []
    for index, row in enumerate(worksheet.rows):
        if index == 0:
            file_titles = list(map(lambda x: x.value, row))
        else:
            row_data = list(map(lambda x: x.value, row))
            row_data = dict(zip(file_titles, row_data))
            if not row_data['Тип'] or row_data['Тип'] == 'Тестовый':
                continue
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
    before_last_month_range_days = monthrange(before_last_month_year, before_last_month)[1]

    before_before_last_month = before_last_month - 1
    before_before_last_month_year = before_last_month_year
    if before_before_last_month == 0:
        before_before_last_month = 12
        before_before_last_month_year -= 1

    before_before_before_last_month = before_last_month - 1
    before_before_before_last_month_year = before_last_month_year
    if before_before_before_last_month == 0:
        before_before_before_last_month = 12
        before_before_before_last_month_year -= 1

    month_filter_start = datetime(day=1, month=report_month, year=report_year)
    month_filter_end = datetime(day=1, month=datetime.now().month, year=datetime.now().year)
    ddmmyyyy_pattern = '%d.%m.%Y'
    if datetime.now().month == 1:
        quarter_filters = get_quarter_filter(12)
    else:
        quarter_filters = get_quarter_filter(datetime.now().month - 1)

    deal_group_field = deal_fields['UF_CRM_1657878818384']['items']
    deal_group_field.append({'ID': None, 'VALUE': 'Лицензии'})
    deal_group_field.append({'ID': None, 'VALUE': 'Остальные'})

    workbook = openpyxl.Workbook()
    report_name = f'Отчет_по_сотрудникам_{datetime.now().strftime("%d_%m_%Y_%H_%M_%S")}.xlsx'
    month_names = {
        1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август', 9: 'Сентябрь',
        10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
    }

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

        last_month_deals_data = read_deals_data_file(report_month, report_year)
        before_last_month_deals_data = read_deals_data_file(before_last_month, before_last_month_year)
        start_year_deals_data = read_deals_data_file(12, datetime.now().year-1)
        '''
        date_quarter = get_quarter_filter(report_month)['start_date'] - timedelta(days=1)
        quarter_deals_data = read_deals_data_file(date_quarter.month, date_quarter.year)
        before_before_last_month_deals_data = read_deals_data_file(before_before_last_month, before_before_last_month_year)
        
        its_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and
                                           x['Группа'] == 'ИТС' and
                                           x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                           last_month_deals_data))

        its_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and
                                                            x['Группа'] == 'ИТС' and
                                                            x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован',
                                                                                   'Счет отправлен клиенту'],
                                                  before_last_month_deals_data))

        its_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and
                                                     x['Группа'] == 'ИТС' and
                                                     x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован',
                                                                            'Счет отправлен клиенту'],
                                           start_year_deals_data))

        # Сделки
        # Отчетный месяц
        its_prof_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and
                                                x['Группа'] == 'ИТС' and
                                                'Базовый' not in x['Тип'] and 'ГРМ' not in x['Тип'] and
                                                x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                last_month_deals_data))

        its_base_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and
                                                x['Группа'] == 'ИТС' and
                                                'Базовый' in x['Тип'] and
                                                x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                last_month_deals_data))

        countragent_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                   'Контрагент' in x['Тип'] and
                                                   x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                   last_month_deals_data))

        spark_in_contract_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                         '1Спарк в договоре' == x['Тип'] and
                                                         x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                         last_month_deals_data))

        spark_3000_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                  ('1Спарк 3000' == x['Тип'] or '1Спарк' == x['Тип']) and
                                                  x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                  last_month_deals_data))

        spark_22500_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                   ('22500' in x['Тип'] or '1СпаркПЛЮС' in x['Тип']) and
                                                   x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                   last_month_deals_data))

        rpd_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                           'РПД' in x['Тип'] and
                                           x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                           last_month_deals_data))

        #добавлено 15-07-2024
        grm_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                           'ГРМ' in x['Тип'] and
                                           x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                           last_month_deals_data))

        doki_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                            'Доки' == x['Тип'] and
                                            x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                            last_month_deals_data))

        report_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                              'Отчетность' in x['Тип'] and
                                              x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                              last_month_deals_data))

        signature_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                 'Подпись' in x['Тип'] and
                                                 x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                 last_month_deals_data))

        dop_oblako_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                  'Допы Облако' == x['Тип'] and
                                                  x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                  last_month_deals_data))

        link_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                            'Линк' == x['Тип'] and
                                            x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                            last_month_deals_data))

        unics_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                             'Уникс' == x['Тип'] and
                                             x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                             last_month_deals_data))

        cab_sotrudnik_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                     'Кабинет сотрудника' == x['Тип'] and
                                                     x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                     last_month_deals_data))

        cab_sadovod_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                   'Кабинет садовода' == x['Тип'] and
                                                   x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                   last_month_deals_data))

        edo_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                           'ЭДО' == x['Тип'] and
                                           x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                           last_month_deals_data))

        mdlp_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                            'МДЛП' == x['Тип'] and
                                            x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                            last_month_deals_data))

        connect_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                               'Коннект' == x['Тип'] and
                                               x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                               last_month_deals_data))

        its_otrasl_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                  'ИТС Отраслевой' == x['Тип'] and
                                                  x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                  last_month_deals_data))

        ofd_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                           'ОФД' == x['Тип'] and
                                           x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                           last_month_deals_data))

        bitrix24_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                ('Битрикс24' == x['Тип'] or 'БИТРИКС24' == x['Тип']) and
                                                x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                last_month_deals_data))

        other_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and
                                             x not in its_prof_deals_last_month and x not in its_base_deals_last_month and
                                             x not in countragent_deals_last_month and x not in spark_in_contract_deals_last_month and
                                             x not in spark_3000_deals_last_month and x not in spark_22500_deals_last_month and
                                             x not in rpd_deals_last_month and x not in grm_deals_last_month and
                                             x not in doki_deals_last_month and
                                             x not in report_deals_last_month and x not in signature_deals_last_month and
                                             x not in dop_oblako_deals_last_month and x not in link_deals_last_month and
                                             x not in unics_deals_last_month and x not in cab_sotrudnik_deals_last_month and
                                             x not in cab_sadovod_deals_last_month and x not in edo_deals_last_month and
                                             x not in mdlp_deals_last_month and x not in connect_deals_last_month and
                                             x not in its_otrasl_deals_last_month and x not in ofd_deals_last_month and
                                             x not in bitrix24_deals_last_month and x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'], last_month_deals_data))

        # Предшествующий отчетному месяц
        its_prof_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and
                                                       x['Группа'] == 'ИТС' and
                                                       'Базовый' not in x['Тип'] and 'ГРМ' not in x['Тип'] and
                                                       x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                       before_last_month_deals_data))

        its_base_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and
                                                       x['Группа'] == 'ИТС' and
                                                       'Базовый' in x['Тип'] and
                                                       x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                       before_last_month_deals_data))

        countragent_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                          'Контрагент' in x['Тип'] and
                                                          x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                          before_last_month_deals_data))

        spark_in_contract_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                                '1Спарк в договоре' == x['Тип'] and
                                                                x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                                before_last_month_deals_data))

        spark_3000_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                         ('1Спарк 3000' == x['Тип'] or '1Спарк' == x['Тип']) and
                                                         x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                         before_last_month_deals_data))

        spark_22500_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                          ('22500' in x['Тип'] or '1СпаркПЛЮС' in x['Тип']) and
                                                          x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                          before_last_month_deals_data))

        rpd_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                  'РПД' in x['Тип'] and
                                                  x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                  before_last_month_deals_data))

        #добавлено 15-07-2024
        grm_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                  'ГРМ' in x['Тип'] and
                                                  x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                  before_last_month_deals_data))

        doki_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                   'Доки' == x['Тип'] and
                                                  x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                  before_last_month_deals_data))

        report_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                     'Отчетность' in x['Тип'] and
                                                     x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                     before_last_month_deals_data))

        signature_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                        'Подпись' in x['Тип'] and
                                                        x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                        before_last_month_deals_data))

        dop_oblako_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                         'Допы Облако' == x['Тип'] and
                                                         x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                         before_last_month_deals_data))

        link_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                   'Линк' == x['Тип'] and
                                                   x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                   before_last_month_deals_data))

        unics_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                    'Уникс' == x['Тип'] and
                                                    x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                    before_last_month_deals_data))

        cab_sotrudnik_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                            'Кабинет сотрудника' == x['Тип'] and
                                                            x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                            before_last_month_deals_data))

        cab_sadovod_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                          'Кабинет садовода' == x['Тип'] and
                                                          x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                          before_last_month_deals_data))

        edo_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                  'ЭДО' == x['Тип'] and
                                                  x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                  before_last_month_deals_data))

        mdlp_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                   'МДЛП' == x['Тип'] and
                                                   x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                   before_last_month_deals_data))

        connect_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                      'Коннект' == x['Тип'] and
                                                      x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                      before_last_month_deals_data))

        its_otrasl_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                         'ИТС Отраслевой' == x['Тип'] and
                                                         x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                         before_last_month_deals_data))

        ofd_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                  'ОФД' == x['Тип'] and
                                                  x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                  before_last_month_deals_data))

        bitrix24_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                       ('Битрикс24' == x['Тип'] or 'БИТРИКС24' == x['Тип']) and
                                                       x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                       before_last_month_deals_data))

        other_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and
                                             x not in its_prof_deals_before_last_month and x not in its_base_deals_before_last_month and
                                             x not in countragent_deals_before_last_month and x not in spark_in_contract_deals_before_last_month and
                                             x not in spark_3000_deals_before_last_month and x not in spark_22500_deals_before_last_month and
                                             x not in rpd_deals_before_last_month and x not in grm_deals_before_last_month and
                                             x not in doki_deals_before_last_month and
                                             x not in report_deals_before_last_month and x not in signature_deals_before_last_month and
                                             x not in dop_oblako_deals_before_last_month and x not in link_deals_before_last_month and
                                             x not in unics_deals_before_last_month and x not in cab_sotrudnik_deals_before_last_month and
                                             x not in cab_sadovod_deals_before_last_month and x not in edo_deals_before_last_month and
                                             x not in mdlp_deals_before_last_month and x not in connect_deals_before_last_month and
                                             x not in its_otrasl_deals_before_last_month and x not in ofd_deals_before_last_month and
                                             x not in bitrix24_deals_before_last_month and x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'], before_last_month_deals_data))

        # Начало квартала
        its_prof_deals_quarter = list(filter(lambda x: x['Ответственный'] == user_name and x['Группа'] == 'ИТС' and
                                             'Базовый' not in x['Тип'] and 'ГРМ' not in x['Тип'] and
                                             x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                             quarter_deals_data))

        its_base_deals_quarter = list(filter(lambda x: x['Ответственный'] == user_name and x['Группа'] == 'ИТС' and
                                             'Базовый' in x['Тип'] and
                                             x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                             quarter_deals_data))

        countragent_deals_quarter = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                'Контрагент' in x['Тип'] and
                                                x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                quarter_deals_data))

        spark_in_contract_deals_quarter = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                      '1Спарк в договоре' == x['Тип'] and
                                                      x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                      quarter_deals_data))

        spark_3000_deals_quarter = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                               ('1Спарк 3000' == x['Тип'] or '1Спарк' == x['Тип']) and
                                               x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                               quarter_deals_data))

        spark_22500_deals_quarter = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                ('22500' in x['Тип'] or '1СпаркПЛЮС' in x['Тип']) and
                                                x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                quarter_deals_data))

        rpd_deals_quarter = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                        'РПД' in x['Тип'] and
                                        x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                        quarter_deals_data))

        #добавлено 15-07-2024
        grm_deals_quarter = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                           'ГРМ' in x['Тип'] and
                                           x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                           quarter_deals_data))

        doki_deals_quarter = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                            'Доки' == x['Тип'] and
                                            x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                            quarter_deals_data))

        report_deals_quarter = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                              'Отчетность' in x['Тип'] and
                                              x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                              quarter_deals_data))

        signature_deals_quarter = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                 'Подпись' in x['Тип'] and
                                                 x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                 quarter_deals_data))

        dop_oblako_deals_quarter = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                  'Допы Облако' == x['Тип'] and
                                                  x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                  quarter_deals_data))

        link_deals_quarter = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                            'Линк' == x['Тип'] and
                                            x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                            quarter_deals_data))

        unics_deals_quarter = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                             'Уникс' == x['Тип'] and
                                             x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                             quarter_deals_data))

        cab_sotrudnik_deals_quarter = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                     'Кабинет сотрудника' == x['Тип'] and
                                                     x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                     quarter_deals_data))

        cab_sadovod_deals_quarter = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                   'Кабинет садовода' == x['Тип'] and
                                                   x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                   quarter_deals_data))

        edo_deals_quarter = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                           'ЭДО' == x['Тип'] and
                                           x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                           quarter_deals_data))

        mdlp_deals_quarter = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                            'МДЛП' == x['Тип'] and
                                            x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                            quarter_deals_data))

        connect_deals_quarter = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                               'Коннект' == x['Тип'] and
                                               x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                               quarter_deals_data))

        its_otrasl_deals_quarter = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                  'ИТС Отраслевой' == x['Тип'] and
                                                  x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                  quarter_deals_data))

        ofd_deals_quarter = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                           'ОФД' == x['Тип'] and
                                           x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                           quarter_deals_data))

        bitrix24_deals_quarter = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                ('Битрикс24' == x['Тип'] or 'БИТРИКС24' == x['Тип']) and
                                                x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                quarter_deals_data))

        other_deals_quarter = list(filter(lambda x: x['Ответственный'] == user_name and
                                             x not in its_prof_deals_quarter and x not in its_base_deals_quarter and
                                             x not in countragent_deals_quarter and x not in spark_in_contract_deals_quarter and
                                             x not in spark_3000_deals_quarter and x not in spark_22500_deals_quarter and
                                             x not in rpd_deals_quarter and x not in grm_deals_quarter and
                                             x not in doki_deals_quarter and
                                             x not in report_deals_quarter and x not in signature_deals_quarter and
                                             x not in dop_oblako_deals_quarter and x not in link_deals_quarter and
                                             x not in unics_deals_quarter and x not in cab_sotrudnik_deals_quarter and
                                             x not in cab_sadovod_deals_quarter and x not in edo_deals_quarter and
                                             x not in mdlp_deals_quarter and x not in connect_deals_quarter and
                                             x not in its_otrasl_deals_quarter and x not in ofd_deals_quarter and
                                             x not in bitrix24_deals_quarter and x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'], quarter_deals_data))

        # Начало года
        its_prof_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and x['Группа'] == 'ИТС' and
                                                'Базовый' not in x['Тип'] and 'ГРМ' not in x['Тип'] and
                                                x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                start_year_deals_data))

        its_base_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and x['Группа'] == 'ИТС' and
                                                'Базовый' in x['Тип'] and
                                                x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                start_year_deals_data))

        countragent_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                   'Контрагент' in x['Тип'] and
                                                   x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                   start_year_deals_data))

        spark_in_contract_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                         '1Спарк в договоре' == x['Тип'] and
                                                         x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                         start_year_deals_data))

        spark_3000_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                  ('1Спарк 3000' == x['Тип'] or '1Спарк' == x['Тип']) and
                                                  x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                  start_year_deals_data))

        spark_22500_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                   ('22500' in x['Тип'] or '1СпаркПЛЮС' in x['Тип']) and
                                                   x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                   start_year_deals_data))

        rpd_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                           'РПД' in x['Тип'] and
                                           x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                           start_year_deals_data))

        #добавлено 15-07-2024
        grm_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                  'ГРМ' in x['Тип'] and
                                                  x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                  start_year_deals_data))

        doki_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                   'Доки' == x['Тип'] and
                                                  x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                  start_year_deals_data))

        report_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                     'Отчетность' in x['Тип'] and
                                                     x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                     start_year_deals_data))

        signature_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                        'Подпись' in x['Тип'] and
                                                        x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                        start_year_deals_data))

        dop_oblako_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                         'Допы Облако' == x['Тип'] and
                                                         x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                         start_year_deals_data))

        link_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                   'Линк' == x['Тип'] and
                                                   x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                   start_year_deals_data))

        unics_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                    'Уникс' == x['Тип'] and
                                                    x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                    start_year_deals_data))

        cab_sotrudnik_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                            'Кабинет сотрудника' == x['Тип'] and
                                                            x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                            start_year_deals_data))

        cab_sadovod_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                          'Кабинет садовода' == x['Тип'] and
                                                          x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                          start_year_deals_data))

        edo_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                  'ЭДО' == x['Тип'] and
                                                  x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                  start_year_deals_data))

        mdlp_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                   'МДЛП' == x['Тип'] and
                                                   x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                   start_year_deals_data))

        connect_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                      'Коннект' == x['Тип'] and
                                                      x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                      start_year_deals_data))

        its_otrasl_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                         'ИТС Отраслевой' == x['Тип'] and
                                                         x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                         start_year_deals_data))

        ofd_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                  'ОФД' == x['Тип'] and
                                                  x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                  start_year_deals_data))

        bitrix24_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                       ('Битрикс24' == x['Тип'] or 'БИТРИКС24' == x['Тип']) and
                                                       x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                       start_year_deals_data))

        other_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and
                                             x not in its_prof_deals_start_year and x not in its_base_deals_start_year and
                                             x not in countragent_deals_start_year and x not in spark_in_contract_deals_start_year and
                                             x not in spark_3000_deals_start_year and x not in spark_22500_deals_start_year and
                                             x not in rpd_deals_start_year and x not in grm_deals_start_year and
                                             x not in doki_deals_start_year and
                                             x not in report_deals_start_year and x not in signature_deals_start_year and
                                             x not in dop_oblako_deals_start_year and x not in link_deals_start_year and
                                             x not in unics_deals_start_year and x not in cab_sotrudnik_deals_start_year and
                                             x not in cab_sadovod_deals_start_year and x not in edo_deals_start_year and
                                             x not in mdlp_deals_start_year and x not in connect_deals_start_year and
                                             x not in its_otrasl_deals_start_year and x not in ofd_deals_start_year and
                                             x not in bitrix24_deals_start_year and x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'], start_year_deals_data))

        worksheet.append(['Сделки', f'на {report_month_last_day_date}', 'Прирост за месяц', 'Прирост с начала квартала',
                          'Прирост с начала года'])
        worksheet.append([
            'ИТС ПРОФ',
            len(its_prof_deals_last_month),
            len(its_prof_deals_last_month) - len(its_prof_deals_before_last_month),
            len(its_prof_deals_last_month) - len(its_prof_deals_quarter),
            len(its_prof_deals_last_month) - len(its_prof_deals_start_year)
        ])
        worksheet.append([
            'ИТС Базовые',
            len(its_base_deals_last_month),
            len(its_base_deals_last_month) - len(its_base_deals_before_last_month),
            len(its_base_deals_last_month) - len(its_base_deals_quarter),
            len(its_base_deals_last_month) - len(its_base_deals_start_year),
        ])
        worksheet.append([
            'Контрагент',
            len(countragent_deals_last_month),
            len(countragent_deals_last_month) - len(countragent_deals_before_last_month),
            len(countragent_deals_last_month) - len(countragent_deals_quarter),
            len(countragent_deals_last_month) - len(countragent_deals_start_year),
        ])
        worksheet.append([
            'Спарк в договоре',
            len(spark_in_contract_deals_last_month),
            len(spark_in_contract_deals_last_month) - len(spark_in_contract_deals_before_last_month),
            len(spark_in_contract_deals_last_month) - len(spark_in_contract_deals_quarter),
            len(spark_in_contract_deals_last_month) - len(spark_in_contract_deals_start_year),
        ])
        worksheet.append([
            #'Спарк 3000',
            'Спарк',
            len(spark_3000_deals_last_month),
            len(spark_3000_deals_last_month) - len(spark_3000_deals_before_last_month),
            len(spark_3000_deals_last_month) - len(spark_3000_deals_quarter),
            len(spark_3000_deals_last_month) - len(spark_3000_deals_start_year),
        ])
        worksheet.append([
            #'СпаркПлюс 22500',
            'СпаркПлюс',
            len(spark_22500_deals_last_month),
            len(spark_22500_deals_last_month) - len(spark_22500_deals_before_last_month),
            len(spark_22500_deals_last_month) - len(spark_22500_deals_quarter),
            len(spark_22500_deals_last_month) - len(spark_22500_deals_start_year),
        ])
        worksheet.append([
            'РПД',
            len(rpd_deals_last_month),
            len(rpd_deals_last_month) - len(rpd_deals_before_last_month),
            len(rpd_deals_last_month) - len(rpd_deals_quarter),
            len(rpd_deals_last_month) - len(rpd_deals_start_year)
        ])
        worksheet.append([
            'ГРМ',
            len(grm_deals_last_month),
            len(grm_deals_last_month) - len(grm_deals_before_last_month),
            len(grm_deals_last_month) - len(grm_deals_quarter),
            len(grm_deals_last_month) - len(grm_deals_start_year)
        ])
        worksheet.append([
            'Доки',
            len(doki_deals_last_month),
            len(doki_deals_last_month) - len(doki_deals_before_last_month),
            len(doki_deals_last_month) - len(doki_deals_quarter),
            len(doki_deals_last_month) - len(doki_deals_start_year)
        ])
        worksheet.append([
            'Отчетности',
            len(report_deals_last_month),
            len(report_deals_last_month) - len(report_deals_before_last_month),
            len(report_deals_last_month) - len(report_deals_quarter),
            len(report_deals_last_month) - len(report_deals_start_year)
        ])
        worksheet.append([
            'Подпись',
            len(signature_deals_last_month),
            len(signature_deals_last_month) - len(signature_deals_before_last_month),
            len(signature_deals_last_month) - len(signature_deals_quarter),
            len(signature_deals_last_month) - len(signature_deals_start_year)
        ])
        worksheet.append([
            'Допы Облако',
            len(dop_oblako_deals_last_month),
            len(dop_oblako_deals_last_month) - len(dop_oblako_deals_before_last_month),
            len(dop_oblako_deals_last_month) - len(dop_oblako_deals_quarter),
            len(dop_oblako_deals_last_month) - len(dop_oblako_deals_start_year)
        ])
        worksheet.append([
            'Линк',
            len(link_deals_last_month),
            len(link_deals_last_month) - len(link_deals_before_last_month),
            len(link_deals_last_month) - len(link_deals_quarter),
            len(link_deals_last_month) - len(link_deals_start_year)
        ])
        worksheet.append([
            'Уникс',
            len(unics_deals_last_month),
            len(unics_deals_last_month) - len(unics_deals_before_last_month),
            len(unics_deals_last_month) - len(unics_deals_quarter),
            len(unics_deals_last_month) - len(unics_deals_start_year)
        ])
        worksheet.append([
            'Кабинет сотрудника',
            len(cab_sotrudnik_deals_last_month),
            len(cab_sotrudnik_deals_last_month) - len(cab_sotrudnik_deals_before_last_month),
            len(cab_sotrudnik_deals_last_month) - len(cab_sotrudnik_deals_quarter),
            len(cab_sotrudnik_deals_last_month) - len(cab_sotrudnik_deals_start_year)
        ])
        worksheet.append([
            'Кабинет садовода',
            len(cab_sadovod_deals_last_month),
            len(cab_sadovod_deals_last_month) - len(cab_sadovod_deals_before_last_month),
            len(cab_sadovod_deals_last_month) - len(cab_sadovod_deals_quarter),
            len(cab_sadovod_deals_last_month) - len(cab_sadovod_deals_start_year)
        ])
        worksheet.append([
            'ЭДО',
            len(edo_deals_last_month),
            len(edo_deals_last_month) - len(edo_deals_before_last_month),
            len(edo_deals_last_month) - len(edo_deals_quarter),
            len(edo_deals_last_month) - len(edo_deals_start_year)
        ])
        worksheet.append([
            'МДЛП',
            len(mdlp_deals_last_month),
            len(mdlp_deals_last_month) - len(mdlp_deals_before_last_month),
            len(mdlp_deals_last_month) - len(mdlp_deals_quarter),
            len(mdlp_deals_last_month) - len(mdlp_deals_start_year)
        ])
        worksheet.append([
            'Коннект',
            len(connect_deals_last_month),
            len(connect_deals_last_month) - len(connect_deals_before_last_month),
            len(connect_deals_last_month) - len(connect_deals_quarter),
            len(connect_deals_last_month) - len(connect_deals_start_year)
        ])
        worksheet.append([
            'ИТС Отраслевой',
            len(its_otrasl_deals_last_month),
            len(its_otrasl_deals_last_month) - len(its_otrasl_deals_before_last_month),
            len(its_otrasl_deals_last_month) - len(its_otrasl_deals_quarter),
            len(its_otrasl_deals_last_month) - len(its_otrasl_deals_start_year)
        ])
        worksheet.append([
            'ОФД',
            len(ofd_deals_last_month),
            len(ofd_deals_last_month) - len(ofd_deals_before_last_month),
            len(ofd_deals_last_month) - len(ofd_deals_quarter),
            len(ofd_deals_last_month) - len(ofd_deals_start_year)
        ])
        if (len(bitrix24_deals_last_month) != 0) or (len(bitrix24_deals_before_last_month) != 0) or (len(bitrix24_deals_quarter) != 0) or (len(bitrix24_deals_start_year) != 0):
            worksheet.append([
                'Битрикс24',
                len(bitrix24_deals_last_month),
                len(bitrix24_deals_last_month) - len(bitrix24_deals_before_last_month),
                len(bitrix24_deals_last_month) - len(bitrix24_deals_quarter),
                len(bitrix24_deals_last_month) - len(bitrix24_deals_start_year)
            ])
        worksheet.append([
            'Прочие',
            len(other_deals_last_month),
            len(other_deals_last_month) - len(other_deals_before_last_month),
            len(other_deals_last_month) - len(other_deals_quarter),
            len(other_deals_last_month) - len(other_deals_start_year)
        ])
        worksheet.append([])

        # Продление
        deals_ended_last_month_dpo = list(filter(lambda x: x['Дата проверки оплаты'] and x['Ответственный'] == user_name, before_before_last_month_deals_data))
        deals_ended_last_month_dk = list(filter(lambda x: x['Ответственный'] == user_name, before_before_last_month_deals_data))
        deals_ended_last_month_dpo = list(map(lambda x: {'ID': x['ID'], 'Дата проверки оплаты': datetime.strptime(x['Дата проверки оплаты'], '%d.%m.%Y %H:%M:%S'), 'Предполагаемая дата закрытия': datetime.strptime(x['Предполагаемая дата закрытия'], '%d.%m.%Y'), 'Группа': x['Группа'], 'Регномер': x['Регномер'], 'Компания': x['Компания'], 'Тип': x['Тип']}, deals_ended_last_month_dpo))
        deals_ended_last_month_dk = list(map(lambda x: {'ID': x['ID'], 'Предполагаемая дата закрытия': datetime.strptime(x['Предполагаемая дата закрытия'], '%d.%m.%Y'), 'Дата проверки оплаты': '', 'Группа': x['Группа'], 'Регномер': x['Регномер'], 'Компания': x['Компания'], 'Тип': x['Тип']}, deals_ended_last_month_dk))
        deals_ended_last_month_dpo = list(filter(lambda x: datetime(day=1, month=before_last_month, year=before_last_month_year) <= x['Дата проверки оплаты'] <= datetime(day=before_last_month_range_days, month=before_last_month, year=before_last_month_year, hour=3), deals_ended_last_month_dpo))
        deals_ended_last_month_dpo_id = list(map(lambda x: x['ID'], deals_ended_last_month_dpo))
        deals_ended_last_month_dk = list(filter(lambda x: x['ID'] not in deals_ended_last_month_dpo_id and (datetime(day=1, month=before_last_month, year=before_last_month_year) <= x['Предполагаемая дата закрытия'] <= datetime(day=before_last_month_range_days, month=before_last_month, year=before_last_month_year)), deals_ended_last_month_dk))
        deals_ended_last_month = deals_ended_last_month_dk + deals_ended_last_month_dpo

        last_month_deals_data_datetime_dpo = list(filter(lambda x: x['Ответственный'] == user_name and x['Дата проверки оплаты'], last_month_deals_data))
        last_month_deals_data_datetime_dpo = list(map(lambda x: {'ID': x['ID'], 'Дата проверки оплаты': datetime.strptime(x['Дата проверки оплаты'], '%d.%m.%Y %H:%M:%S'), 'Предполагаемая дата закрытия': '', 'Стадия': x['Стадия сделки'], 'Регномер': x['Регномер'], 'Компания': x['Компания'], 'Тип': x['Тип']}, last_month_deals_data_datetime_dpo))
        last_month_deals_data_datetime_dk = list(filter(lambda x: x['Ответственный'] == user_name, last_month_deals_data))
        last_month_deals_data_datetime_dk = list(map(lambda x: {'ID': x['ID'], 'Предполагаемая дата закрытия': datetime.strptime(x['Предполагаемая дата закрытия'], '%d.%m.%Y'), 'Дата проверки оплаты': '', 'Стадия': x['Стадия сделки'], 'Регномер': x['Регномер'], 'Компания': x['Компания'], 'Тип': x['Тип']}, last_month_deals_data_datetime_dk))
        non_extended_date_deals = []
        last_month_deals_data_datetime = last_month_deals_data_datetime_dpo + last_month_deals_data_datetime_dk

        for deal in deals_ended_last_month:
            last_month_deal = list(filter(lambda x: x['ID'] == deal['ID'], last_month_deals_data_datetime))
            if not last_month_deal:
                non_extended_date_deals.append(deal)
            else:
                if not last_month_deal[0]['Дата проверки оплаты'] or not deal['Дата проверки оплаты']:
                    continue
                if last_month_deal[0]['Дата проверки оплаты'] <= deal['Дата проверки оплаты'] and last_month_deal[0]['Стадия'] != 'Услуга завершена':
                    non_extended_date_deals.append(deal)

        for deal in deals_ended_last_month:
            if deal in non_extended_date_deals:
                continue
            last_month_deal = list(filter(lambda x: x['ID'] == deal['ID'], last_month_deals_data_datetime))
            if not last_month_deal:
                non_extended_date_deals.append(deal)
            else:
                if not last_month_deal[0]['Предполагаемая дата закрытия']:
                    continue
                if last_month_deal[0]['Предполагаемая дата закрытия'] <= deal['Предполагаемая дата закрытия'] and last_month_deal[0]['Стадия'] != 'Услуга завершена':
                    non_extended_date_deals.append(deal)

        ended_its = set(map(lambda x: x['ID'], list(filter(lambda x: x['Группа'] == 'ИТС', deals_ended_last_month))))
        ended_reporting = set(map(lambda x: x['ID'], list(filter(lambda x: x['Группа'] == 'Сервисы ИТС', deals_ended_last_month))))
        ended_others = set(map(lambda x: x['ID'], list(filter(lambda x: x['Группа'] not in ['Сервисы ИТС', 'ИТС'], deals_ended_last_month))))
        non_extended_date_deals_id = set(map(lambda x: x['ID'], non_extended_date_deals))

        worksheet.append(['Продление', 'Заканчивалось в прошлом месяце', 'Из них продлено', 'Не продлено'])
        worksheet.append([
            'ИТС',
            len(ended_its),
            len(set(filter(lambda x: x not in non_extended_date_deals_id, ended_its))),
            len(set(filter(lambda x: x in non_extended_date_deals_id, ended_its)))
        ])
        worksheet.append([
            'Сервисы',
            len(ended_reporting),
            len(set(filter(lambda x: x not in non_extended_date_deals_id, ended_reporting))),
            len(set(filter(lambda x: x in non_extended_date_deals_id, ended_reporting)))
        ])
        worksheet.append([
            'Остальное',
            len(ended_others),
            len(set(filter(lambda x: x not in non_extended_date_deals_id, ended_others))),
            len(set(filter(lambda x: x in non_extended_date_deals_id, ended_others)))
        ])
        worksheet.append([])

        # Охват сервисами
        # Отчетный месяц
        companies = set(map(lambda x: x['Компания'], list(filter(lambda x: x['Ответственный за компанию'] == user_name, last_month_deals_data))))
        companies_without_services_last_month = 0
        companies_without_paid_services_last_month = 0
        for company in companies:
            company_regnumbers = set(map(lambda x: x['Регномер'], list(filter(lambda x: x['Компания'] == company, last_month_deals_data))))
            company_its = list(filter(lambda x: x['Группа'] == 'ИТС' and company == x['Компания'], last_month_deals_data))
            if not company_its:
                continue

            non_prof_its = list(filter(lambda x: x['Группа'] == 'ИТС' and company == x['Компания'] and 'ПРОФ' not in x['Тип'] and 'Облако' not in x['Тип'] and 'ГРМ' not in x['Тип'], last_month_deals_data))
            if non_prof_its:
                company_its_services = list(filter(lambda x: (company == x['Компания'] or x['Регномер'] in company_regnumbers) and
                                                   ('Контрагент' in x['Тип'] or
                                                   'Спарк' in x['Тип'] or
                                                   'РПД' in x['Тип'] or
                                                   'Отчетность' in x['Тип'] or
                                                   'Допы Облако' in x['Тип'] or
                                                   'Кабинет сотрудника' in x['Тип']),
                                                    last_month_deals_data))

                if not company_its_services:
                    companies_without_services_last_month += 1

            company_its_paid_services = list(filter(lambda x: (company == x['Компания'] or x['Регномер'] in company_regnumbers) and
                                                    ('Контрагент' in x['Тип'] or
                                                    'Спарк' in x['Тип'] or
                                                    'РПД' in x['Тип'] or
                                                    'Отчетность' == x['Тип'] or
                                                    'Допы Облако' in x['Тип'] or
                                                    'Кабинет сотрудника' in x['Тип']), last_month_deals_data))

            if not company_its_paid_services:
                companies_without_paid_services_last_month += 1

        try:
            coverage_its_without_services_last_month = round(round(companies_without_services_last_month /
                                                                    len(its_deals_last_month), 2) * 100, 2)
        except ZeroDivisionError:
            coverage_its_without_services_last_month = 0

        try:
            coverage_its_without_paid_services_last_month = round(round(companies_without_paid_services_last_month /
                                                                    len(its_deals_last_month), 2) * 100, 2)
        except ZeroDivisionError:
            coverage_its_without_paid_services_last_month = 0

        # Предшествующий отчетному месяц
        companies = set(map(lambda x: x['Компания'], list(
            filter(lambda x: x['Ответственный за компанию'] == user_name, before_last_month_deals_data))))
        companies_without_services_before_last_month = 0
        companies_without_paid_services_before_last_month = 0
        for company in companies:
            company_regnumbers = set(map(lambda x: x['Регномер'],
                                         list(filter(lambda x: x['Компания'] == company, before_last_month_deals_data))))
            company_its = list(
                filter(lambda x: x['Группа'] == 'ИТС' and company == x['Компания'], before_last_month_deals_data))
            if not company_its:
                continue

            non_prof_its = list(filter(lambda x: x['Группа'] == 'ИТС' and company == x['Компания'] and 'ПРОФ' not in x[
                'Тип'] and 'Облако' not in x['Тип'] and 'ГРМ' not in x['Тип'], before_last_month_deals_data))
            if non_prof_its:

                company_its_services = list(
                    filter(lambda x: (company == x['Компания'] or x['Регномер'] in company_regnumbers) and
                                     ('Контрагент' in x['Тип'] or
                                      'Спарк' in x['Тип'] or
                                      'РПД' in x['Тип'] or
                                      'Отчетность' in x['Тип'] or
                                      'Допы Облако' in x['Тип'] or
                                      'Кабинет сотрудника' in x['Тип']),
                           before_last_month_deals_data))

                if not company_its_services:
                    companies_without_services_before_last_month += 1

            company_its_paid_services = list(
                filter(lambda x: (company == x['Компания'] or x['Регномер'] in company_regnumbers) and
                                 ('Контрагент' in x['Тип'] or
                                  'Спарк' in x['Тип'] or
                                  'РПД' in x['Тип'] or
                                  'Отчетность' == x['Тип'] or
                                  'Допы Облако' in x['Тип'] or
                                  'Кабинет сотрудника' in x['Тип']), before_last_month_deals_data))

            if not company_its_paid_services:
                companies_without_paid_services_before_last_month += 1

        try:
            coverage_its_without_services_before_last_month = round(round(companies_without_services_before_last_month /
                                                                   len(its_deals_before_last_month), 2) * 100, 2)
        except ZeroDivisionError:
            coverage_its_without_services_before_last_month = 0

        try:
            coverage_its_without_paid_services_before_last_month = round(round(companies_without_paid_services_before_last_month /
                                                                        len(its_deals_before_last_month), 2) * 100, 2)
        except ZeroDivisionError:
            coverage_its_without_paid_services_before_last_month = 0

        # Начало года
        companies = set(map(lambda x: x['Компания'], list(
            filter(lambda x: x['Ответственный за компанию'] == user_name, start_year_deals_data))))
        companies_without_services_start_year = 0
        companies_without_paid_services_start_year = 0
        for company in companies:
            company_regnumbers = set(map(lambda x: x['Регномер'],
                                         list(filter(lambda x: x['Компания'] == company,
                                                     start_year_deals_data))))
            company_its = list(
                filter(lambda x: x['Группа'] == 'ИТС' and company == x['Компания'], start_year_deals_data))
            if not company_its:
                continue

            non_prof_its = list(filter(lambda x: x['Группа'] == 'ИТС' and company == x['Компания'] and 'ПРОФ' not in x[
                'Тип'] and 'Облако' not in x['Тип'] and 'ГРМ' not in x['Тип'], start_year_deals_data))

            if non_prof_its:
                company_its_services = list(
                    filter(lambda x: (company == x['Компания'] or x['Регномер'] in company_regnumbers) and
                                     ('Контрагент' in x['Тип'] or
                                      'Спарк' in x['Тип'] or
                                      'РПД' in x['Тип'] or
                                      'Отчетность' in x['Тип'] or
                                      'Допы Облако' in x['Тип'] or
                                      'Кабинет сотрудника' in x['Тип']),
                           start_year_deals_data))

                if not company_its_services:
                    companies_without_services_start_year += 1

            company_its_paid_services = list(
                filter(lambda x: (company == x['Компания'] or x['Регномер'] in company_regnumbers) and
                                 ('Контрагент' in x['Тип'] or
                                  'Спарк' in x['Тип'] or
                                  'РПД' in x['Тип'] or
                                  'Отчетность' == x['Тип'] or
                                  'Допы Облако' in x['Тип'] or
                                  'Кабинет сотрудника' in x['Тип']), start_year_deals_data))

            if not company_its_paid_services:
                companies_without_paid_services_start_year += 1

        try:
            coverage_its_without_services_start_year = round(
                round(companies_without_services_start_year /
                      len(its_deals_start_year), 2) * 100, 2)
        except ZeroDivisionError:
            coverage_its_without_services_start_year = 0

        try:
            coverage_its_without_paid_services_start_year = round(
                round(companies_without_paid_services_start_year /
                      len(its_deals_start_year), 2) * 100, 2)
        except ZeroDivisionError:
            coverage_its_without_paid_services_start_year = 0



        worksheet.append(['Охват сервисами', f'на {report_month_last_day_date}', 'Прирост за месяц',
                          'Прирост с начала года', 'На начало года'])
        worksheet.append([
            'ИТС без сервисов',
            companies_without_services_last_month,
            companies_without_services_last_month - companies_without_services_before_last_month,
            companies_without_services_last_month - companies_without_services_start_year,
            companies_without_services_start_year
        ])
        worksheet.append([
            '% ИТС без сервисов',
            f'{coverage_its_without_services_last_month}%',
            f'{coverage_its_without_services_last_month - coverage_its_without_services_before_last_month}%',
            f'{coverage_its_without_services_last_month - coverage_its_without_services_start_year}%',
            f'{coverage_its_without_services_start_year}%'
        ])
        worksheet.append([
            'ИТС без платных сервисов',
            companies_without_paid_services_last_month,
            companies_without_paid_services_last_month - companies_without_paid_services_before_last_month,
            companies_without_paid_services_last_month - companies_without_paid_services_start_year,
            companies_without_paid_services_start_year
        ])
        worksheet.append([
            '% ИТС без платных сервисов',
            f'{coverage_its_without_paid_services_last_month}%',
            f'{coverage_its_without_paid_services_last_month - coverage_its_without_paid_services_before_last_month}%',
            f'{coverage_its_without_paid_services_last_month - coverage_its_without_paid_services_start_year}%',
            f'{coverage_its_without_paid_services_start_year}%',
        ])
        worksheet.append([])

       # Отчетность
        # Отчетный месяц
        free_reporting_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and
                                                      x['Тип'] == 'Отчетность (в рамках ИТС)' and
                                                      x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                      last_month_deals_data))

        try:
            coverage_free_reporting_deals_last_month = round(len(free_reporting_deals_last_month) /
                                                             len(its_prof_deals_last_month), 2) * 100
        except ZeroDivisionError:
            coverage_free_reporting_deals_last_month = 0

        paid_reporting_deals_last_month_num = 0 #>ibs 20240330
        paid_reporting_deals_last_month = 0
        for its_deal in its_deals_last_month:
            its_paid_reporting = list(filter(lambda x: (x['Регномер'] == its_deal['Регномер'] and x['Тип'] == 'Отчетность' and x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту']), last_month_deals_data))
            if its_paid_reporting:
                paid_reporting_deals_last_month += 1
                for i in range(len(its_paid_reporting)): #>ibs 20240330
                    paid_reporting_deals_last_month_num +=1 #>ibs 20240330
        try:
            coverage_paid_reporting_deals_last_month = round(round(paid_reporting_deals_last_month /
                                                             len(its_deals_last_month), 2) * 100, 2)
        except ZeroDivisionError:
            coverage_paid_reporting_deals_last_month = 0
        
        # ibs 20240330>
        any_reporting_deals_last_month = 0
        for its_deal in its_deals_last_month:
            any_reporting = list(filter(lambda x: (x['Регномер'] == its_deal['Регномер'] and 'Отчетность' in x['Тип'] and x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту']),last_month_deals_data))
            if any_reporting:
                any_reporting_deals_last_month += 1
        try:
            coverage_any_reporting_deals_last_month = round(round(any_reporting_deals_last_month /
                                                             len(its_deals_last_month), 2) * 100, 2)
        except ZeroDivisionError:
            coverage_any_reporting_deals_last_month = 0
        # >ibs 20240330

        
        #любая отчетность за прошлый месяц 28-03-2024
        regnumbers = set(map(lambda x: x['Регномер'], its_deals_last_month))
        deals_last_month = set(map(lambda x: x['Регномер'] and x['Тип'], other_deals_last_month))
        any_reporting_deals_last_month = 0
        for regnum in regnumbers:
            regnum.strip()
            any_reporting = list(filter(lambda x: regnum == str(x['Регномер']).strip() and 'Отчетность' in x['Тип'], deals_last_month))
            if any_reporting:
                #print(regnum, len(any_reporting))
                any_reporting_deals_last_month += 1

        try:
            coverage_any_reporting_deals_last_month = round(round(any_reporting_deals_last_month /
                                                             len(its_deals_last_month), 2) * 100, 2)
        except ZeroDivisionError:
            coverage_any_reporting_deals_last_month = 0
        

        # Предшествующий отчетному месяц
        free_reporting_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and
                                                             x['Тип'] == 'Отчетность (в рамках ИТС)' and
                                                             x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                             before_last_month_deals_data))

        try:
            coverage_free_reporting_deals_before_last_month = round(round(len(free_reporting_deals_before_last_month) /
                                                                    len(its_prof_deals_before_last_month), 2) * 100, 2)
        except ZeroDivisionError:
            coverage_free_reporting_deals_before_last_month = 0

        paid_reporting_deals_before_last_month = 0
        paid_reporting_deals_before_last_month_num = 0 #>ibs 20240330
        for its_deal in its_deals_before_last_month:
            its_paid_reporting = list(
                filter(lambda x: (x['Регномер'] == its_deal['Регномер'] and x['Тип'] == 'Отчетность' and x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту']),
                       before_last_month_deals_data))
            if its_paid_reporting:
                paid_reporting_deals_before_last_month += 1
                for i in range(len(its_paid_reporting)): #>ibs 20240330
                    paid_reporting_deals_before_last_month_num +=1 #>ibs 20240330
        try:
            coverage_paid_reporting_deals_before_last_month = round(round(paid_reporting_deals_before_last_month /
                                                                    len(its_deals_before_last_month), 2) * 100, 2)
        except ZeroDivisionError:
            coverage_paid_reporting_deals_before_last_month = 0
        # ibs 20240330>
        any_reporting_deals_before_last_month = 0
        for its_deal in its_deals_before_last_month:
            any_reporting = list(filter(lambda x: (x['Регномер'] == its_deal['Регномер'] and 'Отчетность' in x['Тип'] and x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту']), before_last_month_deals_data))
            if any_reporting:
                any_reporting_deals_before_last_month += 1
        try:
            coverage_any_reporting_deals_before_last_month = round(round(any_reporting_deals_before_last_month /
                                                             len(its_deals_before_last_month), 2) * 100, 2)
        except ZeroDivisionError:
            coverage_any_reporting_deals_before_last_month = 0
        # >ibs  20240330

        
        #любая отчетность за позапрошлый месяц 28-03-2024
        regnumbers = set(map(lambda x: x['Регномер'], its_deals_before_last_month))
        any_reporting_deals_before_last_month = 0
        for regnum in regnumbers:
            regnum.strip()
            any_reporting = list(filter(lambda x: regnum == x['Регномер'] and 'Отчетность' in x['Тип'], other_deals_before_last_month))
            if any_reporting:
                any_reporting_deals_before_last_month += 1

        try:
            coverage_any_reporting_deals_before_last_month = round(round(any_reporting_deals_before_last_month /
                                                             len(its_deals_before_last_month), 2) * 100, 2)
        except ZeroDivisionError:
            coverage_any_reporting_deals_before_last_month = 0
        

        # Начало года
        free_reporting_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and
                                                      x['Тип'] == 'Отчетность (в рамках ИТС)' and
                                                      x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                      start_year_deals_data))

        prof_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and
                                            x['Группа'] == 'ИТС' and
                                            'Базовый' not in x['Тип'] and
                                            x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                            start_year_deals_data))

        try:
            coverage_free_reporting_deals_start_year = round(round(len(free_reporting_deals_start_year) /
                                                             len(prof_deals_start_year), 2) * 100, 2)
        except ZeroDivisionError:
            coverage_free_reporting_deals_start_year = 0

        paid_reporting_deals_start_year = 0
        paid_reporting_deals_start_year_num = 0 #>ibs 20240330
        for its_deal in its_deals_start_year:
            its_paid_reporting = list(
                filter(lambda x: (x['Регномер'] == its_deal['Регномер'] and x['Тип'] == 'Отчетность' and x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту']),
                       start_year_deals_data))
            if its_paid_reporting:
                paid_reporting_deals_start_year += 1
                for i in range(len(its_paid_reporting)): #>ibs 20240330
                    paid_reporting_deals_start_year_num +=1 #>ibs 20240330
        try:
            coverage_paid_reporting_deals_start_year = round(round(paid_reporting_deals_start_year /
                                                             len(its_deals_start_year), 2) * 100, 2)
        except ZeroDivisionError:
            coverage_paid_reporting_deals_start_year = 0

        # ibs> 20240330
        any_reporting_deals_start_year  = 0
        for its_deal in its_deals_start_year:
            any_reporting = list(filter(lambda x: (x['Регномер'] == its_deal['Регномер'] and 'Отчетность' in x['Тип'] and x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту']), start_year_deals_data))
            if any_reporting:
                any_reporting_deals_start_year  += 1
        try:
            coverage_any_reporting_deals_start_year = round(round(any_reporting_deals_start_year /
                                                             len(its_deals_start_year), 2) * 100, 2)
        except ZeroDivisionError:
            coverage_any_reporting_deals_start_year = 0
        # >ibs 20240330
        
        
        #любая отчетность на начало года 28-03-2024
        regnumbers = set(map(lambda x: x['Регномер'], its_deals_start_year))
        any_reporting_deals_start_year = 0
        for regnum in regnumbers:
            regnum.strip()
            any_reporting = list(filter(lambda x: regnum == x['Регномер'] and 'Отчетность' in x['Тип'], other_deals_start_year))
            if any_reporting:
                any_reporting_deals_start_year += 1

        try:
            coverage_any_reporting_deals_start_year = round(round(any_reporting_deals_start_year /
                                                            len(its_deals_start_year), 2) * 100, 2)
        except ZeroDivisionError:
            coverage_any_reporting_deals_start_year = 0
        

        worksheet.append(['Отчетность', f'на {report_month_last_day_date}', 'Прирост за месяц', 'Прирост с начала года',
                          'Количество на январь'])
        worksheet.append([
            'Льготных отчетностей',
            len(free_reporting_deals_last_month),
            len(free_reporting_deals_last_month) - len(free_reporting_deals_before_last_month),
            len(free_reporting_deals_last_month) - len(free_reporting_deals_start_year),
            len(free_reporting_deals_start_year),
        ])
        worksheet.append([
            'Охват льготной отчетностью',
            f'{round(coverage_free_reporting_deals_last_month, 2)}%',
            f'{round(coverage_free_reporting_deals_last_month - coverage_free_reporting_deals_before_last_month, 2)}%',
            f'{round(coverage_free_reporting_deals_last_month - coverage_free_reporting_deals_start_year, 2)}%',
            f'{round(coverage_free_reporting_deals_start_year, 2)}%',
        ])
        #ibs 20240330>
        worksheet.append([
            'Сделок платных отчетностей',
            paid_reporting_deals_last_month_num,
            paid_reporting_deals_last_month_num - paid_reporting_deals_before_last_month_num,
            paid_reporting_deals_last_month_num - paid_reporting_deals_start_year_num,
            paid_reporting_deals_start_year_num,
        ])
        #>ibs  20240330
        worksheet.append([
            'ИТС с платной отчетностью',
            paid_reporting_deals_last_month,
            paid_reporting_deals_last_month - paid_reporting_deals_before_last_month,
            paid_reporting_deals_last_month - paid_reporting_deals_start_year,
            paid_reporting_deals_start_year,
        ])
        worksheet.append([
            'Охват платных отчетностей',
            f'{round(coverage_paid_reporting_deals_last_month, 2)}%',
            f'{round(coverage_paid_reporting_deals_last_month - coverage_paid_reporting_deals_before_last_month, 2)}%',
            f'{round(coverage_paid_reporting_deals_last_month - coverage_paid_reporting_deals_start_year, 2)}%',
            f'{round(coverage_paid_reporting_deals_start_year, 2)}%',
        ])

        worksheet.append([
            'Любая отчетность',
            any_reporting_deals_last_month,
            any_reporting_deals_last_month - any_reporting_deals_before_last_month,
            any_reporting_deals_last_month - any_reporting_deals_start_year,
            any_reporting_deals_start_year,
        ])
        worksheet.append([
            'Охват любой отчетностью',
            f'{round(coverage_any_reporting_deals_last_month, 2)}%',
            f'{round(coverage_any_reporting_deals_last_month - coverage_any_reporting_deals_before_last_month, 2)}%',
            f'{round(coverage_any_reporting_deals_last_month - coverage_any_reporting_deals_start_year, 2)}%',
            f'{round(coverage_any_reporting_deals_start_year, 2)}%',
        ])

        worksheet.append([])
        '''
        #Апсейл
        last_month_filter = datetime(day=1, month=before_last_month, year=before_last_month_year)
        upsale = b.get_all('crm.item.list', {
            'entityTypeId': '1094',
            'filter': {
                'assignedById': user_info['ID'],
                '>=ufCrm83_DateUpsale': last_month_filter.strftime(ddmmyyyy_pattern),
                '<ufCrm83_DateUpsale': month_filter_end.strftime(ddmmyyyy_pattern),
            }
        })

        if upsale: 
            print(datetime.fromisoformat(day=1, month=report_month, year=report_year, hour=3))
            print(datetime.fromisoformat(day=1, month=datetime.now().month, year=datetime.now().year, hour=3))
            print(upsale[0]['ufCrm83DateUpsale'])
            actual_upsale = list(filter(lambda x: datetime.fromisoformat(day=1, month=report_month, year=report_year, hour=3)
                                        <= x['ufCrm83DateUpsale']
                                        < datetime.fromisoformat(day=1, month=datetime.now().month, year=datetime.now().year, hour=3), upsale))[0]
            actual_sumserv = actual_upsale['ufCrm83_SumServices']
            actual_averits = actual_upsale['ufCrm83_AverageIts']
            actual_sumup = actual_upsale['ufCrm83_SumUpsale']

            if not actual_upsale:
                actual_sumserv = 0
                actual_averits = 0
                actual_sumup = 0

            last_upsale = list(filter(lambda x: datetime(day=1, month=before_last_month, year=before_last_month_year, hour=3)
                                        <= x['ufCrm83DateUpsale']
                                        < datetime(day=1, month=report_month, year=report_year, hour=3), upsale))[0]
            last_sumserv = last_upsale['ufCrm83_SumServices']
            last_averits = last_upsale['ufCrm83_AverageIts']
            last_sumup = last_upsale['ufCrm83_SumUpsale']

            if not last_upsale:
                last_sumserv = 0
                last_averits = 0
                last_sumup = 0
        else:
            actual_sumserv = 0
            actual_averits = 0
            actual_sumup = 0
            last_sumserv = 0
            last_averits = 0
            last_sumup = 0

        worksheet.append(['Апсейл', f'{month_names[report_month]} {report_year}', f'{month_names[before_last_month]} {report_year}'])
        worksheet.append(['Сумма сервисов', actual_sumserv, last_sumserv])
        worksheet.append(['Средний ИТС', actual_averits, last_averits])
        worksheet.append(['Апсейл', actual_sumup, last_sumup])
        worksheet.append([])

        '''    
        # Продажи
        sales = b.get_all('crm.item.list', {
            'entityTypeId': '133',
            'filter': {
                'assignedById': user_info['ID'],
                '>=ufCrm3_1654248264': month_filter_start.strftime(ddmmyyyy_pattern),
                '<ufCrm3_1654248264': month_filter_end.strftime(ddmmyyyy_pattern),
            }
        })

        oldsales = b.get_all('crm.item.list', {
            'entityTypeId': '133',
            'filter': {
                'assignedById': user_info['ID'],
                '>=createdTime': month_filter_start.strftime(ddmmyyyy_pattern),
                '<createdTime': month_filter_end.strftime(ddmmyyyy_pattern),
                '<ufCrm3_1654248264': month_filter_start.strftime(ddmmyyyy_pattern),
            }
        })

        list_of_sales = ([{'NAME_DEAL': 'Название сделки', 'COMPANY': 'Компания', 'OPPORTUNITY': 'Сумма'}])
        list_of_oldsales = ([{'DATE_SALE': 'Дата продажи', 'NAME_DEAL': 'Название сделки', 'COMPANY': 'Компания', 'OPPORTUNITY': 'Сумма'}])

        all_sales = sales + oldsales

        if all_sales:
            deals = b.get_all('crm.deal.list', {
                'select': ['ID', 'COMPANY_ID', 'UF_CRM_1657878818384', 'OPPORTUNITY', 'TYPE_ID'],
                'filter': {
                    'ID': list(map(lambda x: x['parentId2'], all_sales))
                }
            })

            company_titles = b.get_all('crm.company.list', {
                'select': ['ID', 'TITLE'],
                'filter': {
                    'ID': list(map(lambda x: x['COMPANY_ID'], deals))
                }
            })

            #источники внесенные вовремя
            if sales:
                deal_ids_new = {int(sale['parentId2']) for sale in sales if sale['parentId2'] is not None}
                if deal_ids_new:
                    sold_deals = list(filter(lambda x: int(x['ID']) in deal_ids_new, deals))

                    for sale in sales:
                        try:
                            title_deal = list(filter(lambda x: int(x['ID']) == sale['parentId2'], last_month_deals_data))[0]['Название сделки']
                            title_company = list(set(map(lambda x: x['TITLE'], list(filter(lambda x: int(x['ID']) == sale['companyId'], company_titles)))))[0]
                            list_of_sales.append({'NAME_DEAL': title_deal, 'COMPANY': title_company, 'OPPORTUNITY': sale['opportunity']})
                        except:
                            users_id = ['1391', '1'] # , '1'
                            for user_id in users_id:
                                b.call('im.notify.system.add', {
                                    'USER_ID': user_id,
                                    'MESSAGE': f'Проблемы при поиске сделки (id = {sale["parentId2"]}) в файле по источнику продаж (id = {sale["id"]})'})


            else:
                sold_deals = []

            #источники внесенные НЕ вовремя
            if oldsales:
                deal_ids_old = {int(sale['parentId2']) for sale in oldsales if sale['parentId2'] is not None}
                if deal_ids_old:

                    for oldsale in oldsales:
                        try:
                            title_deal = list(filter(lambda x: int(x['ID']) == oldsale['parentId2'], last_month_deals_data))[0]['Название сделки']
                            title_company = list(set(map(lambda x: x['TITLE'], list(filter(lambda x: int(x['ID']) == oldsale['companyId'], company_titles)))))[0]
                            date_sale = datetime.fromisoformat(oldsale['ufCrm3_1654248264'])
                            date_sale = date_sale.strftime(ddmmyyyy_pattern)
                            list_of_oldsales.append({'DATE_SALE': date_sale, 'NAME_DEAL': title_deal, 'COMPANY': title_company, 'OPPORTUNITY': oldsale['opportunity']})
                        except:
                            users_id = ['1391', '1']
                            for user_id in users_id:
                                b.call('im.notify.system.add', {
                                    'USER_ID': user_id,
                                    'MESSAGE': f'Проблемы при поиске сделки (id = {oldsale["parentId2"]}) в файле по старому источнику продаж (id = {oldsale["id"]})'})

        else:
            sold_deals = []

        worksheet.append(['Продажи', f'{month_names[report_month]} {report_year} шт.', f'{month_names[report_month]} {report_year} руб'])
        for field_value in deal_group_field:
            if field_value['VALUE'] == 'Лицензии':
                grouped_deals = list(filter(lambda x: x['TYPE_ID'] in ['UC_YIAJC8', 'UC_QQPYF0'], sold_deals))
            else:
                grouped_deals = list(filter(lambda x: x['UF_CRM_1657878818384'] == field_value['ID'] and x['TYPE_ID'] not in ['UC_YIAJC8', 'UC_QQPYF0'], sold_deals))
            worksheet.append([field_value['VALUE'], len(grouped_deals), sum(list(map(lambda x: float(x['OPPORTUNITY'] if x['OPPORTUNITY'] else 0.0), grouped_deals)))])
        worksheet.append(['Всего по источникам', len(sales), sum(list(map(lambda x: x['opportunity'], sales)))])
        worksheet.append(['Всего по сделкам', len(sold_deals), sum(list(map(lambda x: float(x['OPPORTUNITY']), sold_deals)))])
        worksheet.append([])

        #детализация по новым продажам в источниках со сделками
        if len(list_of_sales) > 1:
            worksheet.append(['', 'Перечень продаж', ''])
            for selling in list_of_sales:
                worksheet.append([selling['NAME_DEAL'], selling['COMPANY'], selling['OPPORTUNITY']])
            worksheet.append([])

        #детализация по старым продажам в источниках со сделками
        if len(list_of_oldsales) > 1:
            worksheet.append(['', 'Перечень старых продаж', ''])
            for selling in list_of_oldsales:
                worksheet.append([selling['DATE_SALE'], selling['NAME_DEAL'], selling['COMPANY'], selling['OPPORTUNITY']])
            worksheet.append([])
        
        # Долги по документам
        documents_debts = b.get_all('crm.item.list', {
            'entityTypeId': '161',
            'filter': {
                'assignedById': user_info['ID'],
                'stageId': ['DT161_53:NEW', 'DT161_53:1'],
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

        #Разовые услуги
        provide_services = b.get_all('crm.item.list', {
            'entityTypeId': 161,
            'select': ['assignedById', 'ufCrm41_Provider', 'ufCrm41_1689101328', 'ufCrm41_1690546413', 'ufCrm41_1761298275'],
            'filter': {
                'ufCrm41_Provider': float(user_info['ID']),
                '>=ufCrm41_1689101272': month_filter_start.strftime(ddmmyyyy_pattern),
                '<ufCrm41_1689101272': month_filter_end.strftime(ddmmyyyy_pattern)
            }
        })

        sold_services = b.get_all('crm.item.list', {
            'entityTypeId': 161,
            'select': ['assignedById', 'ufCrm41_Provider', 'ufCrm41_1689101328'],
            'filter': {
                '!ufCrm41_ProviderId': False,
                'assignedById': float(user_info['ID']),
                '>=ufCrm41_1689101272': month_filter_start.strftime(ddmmyyyy_pattern),
                '<ufCrm41_1689101272': month_filter_end.strftime(ddmmyyyy_pattern)
            }
        })

        #provide_services = list(filter(lambda x: x['ufCrm41_Provider'] == float(user_info['ID']), single_service))
        sum_provide_services = sum(list(map(lambda x: float(x['ufCrm41_1689101328'] if x['ufCrm41_1689101328'] else 0.0), provide_services)))

        if provide_services:
            list_provide_services = ([{'COMPANY': 'Компания', 'TYPE_PAY': 'Вид расчета', 'OPPORTUNITY': 'Сумма'}]) # 'TYPE_PAY': 'Вид расчета', 
            for pr_service in provide_services:
                list_provide_services.append({'COMPANY': pr_service['ufCrm41_1690546413'], 
                                              'TYPE_PAY': pr_service['ufCrm41_1761298275'], # 'TYPE_PAY': pr_service['ufCrm41_1761298275'],
                                              'OPPORTUNITY': pr_service['ufCrm41_1689101328']}) 

        #sold_services = list(filter(lambda x: x['assignedById'] == user_info['ID'], single_service))
        sum_sold_services = sum(list(map(lambda x: float(x['ufCrm41_1689101328'] if x['ufCrm41_1689101328'] else 0.0), sold_services)))
        
        worksheet.append(['Разовые услуги, за месяц', 'Оказано услуг', 'Продано услуг'])
        worksheet.append(['Кол-во', len(provide_services), len(sold_services)])
        worksheet.append(['Сумма', sum_provide_services, sum_sold_services])

        #детализация по оказанным услугам
        if len(provide_services) > 1:
            worksheet.append(['', 'Выполненные работы', ''])
            for service in list_provide_services:
                worksheet.append([service['COMPANY'], service['TYPE_PAY'], service['OPPORTUNITY']]) # service['TYPE_PAY'], 
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

        #Попытка Дежурства
        days_duty = b.get_all('lists.element.get', {
            'IBLOCK_TYPE_ID': 'lists',
            'IBLOCK_ID': '301',
            'filter': {
                'PROPERTY_1753': user_info['ID'],
                'PROPERTY_1769': int(report_month),
                'PROPERTY_1771': int(report_year),
            }
        })
        days_duty_amount = len(days_duty)
        print(days_duty_amount)

        worksheet.append(['', 'Незакрытых (и созд. в этом мес)', 'Всего создано в месяце'])
        worksheet.append(['Незакрытые задачи', len(tasks) - len(completed_tasks), len(tasks)])
        worksheet.append(['СВ', len(service_tasks) - len(completed_service_tasks), len(service_tasks)])
        worksheet.append(['Остальные', len(non_completed_other_tasks), len(completed_other_tasks) + len(non_completed_other_tasks)])
        worksheet.append([])
        worksheet.append(['Закрытые задачи ТЛП', len(completed_tlp_tasks)])
        worksheet.append(['Средняя оценка', average_tasks_ratings])
        worksheet.append(['Дней дежурства', days_duty_amount])
        worksheet.append([])

        change_sheet_style(worksheet)
        
        # ЭДО
        all_its = its_prof_deals_last_month + its_base_deals_last_month
        edo_companies_id = list(map(lambda x: x['Компания'], list(filter(lambda y: 'Компания' in y and y['Компания'], all_its))))

        if edo_companies_id:
            edo_companies = b.get_all('crm.company.list', {
                'select': ['UF_CRM_1638093692254', 'UF_CRM_1638093750742'],
                'filter': {
                    'ID': list(map(lambda x: x['Компания'], list(filter(lambda y: 'Компания' in y and y['Компания'], all_its))))
                }
            })
            edo_companies_count = list(filter(lambda x: x['UF_CRM_1638093692254'] == '69', edo_companies))

            #спецоператоры эдо
            try: 
                operator_2ae = list(filter(lambda x: x['UF_CRM_1638093750742'] == '75', edo_companies_count))
            except ZeroDivisionError:
                operator_2ae = 0
            try: 
                operator_2ae_doki = list(filter(lambda x: x['UF_CRM_1638093750742'] == '1715', edo_companies_count))
            except ZeroDivisionError:
                operator_2ae_doki = 0
            try: 
                operator_2be = list(filter(lambda x: x['UF_CRM_1638093750742'] == '77', edo_companies_count))
            except ZeroDivisionError:
                operator_2be = 0
            try: 
                operator_2bm = list(filter(lambda x: x['UF_CRM_1638093750742'] == '73', edo_companies_count))
            except ZeroDivisionError:
                operator_2bm = 0
            try: 
                operator_2al = list(filter(lambda x: x['UF_CRM_1638093750742'] == '437', edo_companies_count))
            except ZeroDivisionError:
                operator_2al = 0
            try: 
                operator_2lb = list(filter(lambda x: x['UF_CRM_1638093750742'] == '439', edo_companies_count))
            except ZeroDivisionError:
                operator_2lb = 0
            try: 
                operator_2bk = list(filter(lambda x: x['UF_CRM_1638093750742'] == '1357', edo_companies_count))
            except ZeroDivisionError:
                operator_2bk = 0
            try: 
                operator_2lt = list(filter(lambda x: x['UF_CRM_1638093750742'] == '1831', edo_companies_count))
            except ZeroDivisionError:
                operator_2lt = 0

            edo_elements_info = b.get_all('lists.element.get', {
                'IBLOCK_TYPE_ID': 'lists',
                'IBLOCK_ID': '235',
                'filter': {
                    'PROPERTY_1579': edo_companies_id,
                    'PROPERTY_1567': month_codes[month_int_names[report_month]],
                    'PROPERTY_1569': year_codes[str(report_year)],
                }
            })
            edo_elements_info = list(map(lambda x: {
                'ID': x['ID'],
                'Компания': list(x['PROPERTY_1579'].values())[0],
                'Сумма пакетов по владельцу': int(list(x['PROPERTY_1573'].values())[0]),
                'Сумма для клиента': int(list(x['PROPERTY_1575'].values())[0]),
            }, edo_elements_info))
            traffic_more_than_1 = list(filter(lambda x: x['Сумма пакетов по владельцу'] > 1, edo_elements_info))
            edo_elements_paid = b.get_all('lists.element.get', {
                'IBLOCK_TYPE_ID': 'lists',
                'IBLOCK_ID': '235',
                'filter': {
                    'PROPERTY_1581': user_info['ID'],
                    'PROPERTY_1567': month_codes[month_int_names[report_month]],
                    'PROPERTY_1569': year_codes[str(report_year)],
                }
            })

            paid_traffic = list(filter(lambda x: int(list(x['PROPERTY_1573'].values())[0]) > 0 and int(list(x['PROPERTY_1575'].values())[0]) > 0, edo_elements_paid))
            paid_traffic = sum(list(map(lambda x: int(list(x['PROPERTY_1575'].values())[0]), paid_traffic)))

        else:
            edo_companies_count = []
            traffic_more_than_1 = []
            paid_traffic = 0
            operator_2ae = []
            operator_2ae_doki = []
            operator_2be = []
            operator_2bm = []
            operator_2al = []
            operator_2lb = []
            operator_2bk = []
            operator_2lt = []

        try:
            edo_companies_coverage = round((len(edo_companies_count) / len(all_its)) * 100, 2)
        except ZeroDivisionError:
            edo_companies_coverage = 0

        try:
            active_its_coverage = round((len(traffic_more_than_1) / len(all_its)) * 100, 2)
        except ZeroDivisionError:
            active_its_coverage = 0

        try:
            operator_2ae_coverage = round((len(operator_2ae) / len(edo_companies_count)) * 100, 2)
        except ZeroDivisionError:
            operator_2ae_coverage = 0
        try:
            operator_2ae_doki_coverage = round((len(operator_2ae_doki) / len(edo_companies_count)) * 100, 2)
        except ZeroDivisionError:
            operator_2ae_doki_coverage = 0
        try:
            operator_2be_coverage = round((len(operator_2be) / len(edo_companies_count)) * 100, 2)
        except ZeroDivisionError:
            operator_2be_coverage = 0
        try:
            operator_2bm_coverage = round((len(operator_2bm) / len(edo_companies_count)) * 100, 2)
        except ZeroDivisionError:
            operator_2bm_coverage = 0
        try:
            operator_2al_coverage = round((len(operator_2al) / len(edo_companies_count)) * 100, 2)
        except ZeroDivisionError:
            operator_2al_coverage = 0
        try:
            operator_2lb_coverage = round((len(operator_2lb) / len(edo_companies_count)) * 100, 2)
        except ZeroDivisionError:
            operator_2lb_coverage = 0
        try:
            operator_2bk_coverage = round((len(operator_2bk) / len(edo_companies_count)) * 100, 2)
        except ZeroDivisionError:
            operator_2bk_coverage = 0
        try:
            operator_2lt_coverage = round((len(operator_2lt) / len(edo_companies_count)) * 100, 2)
        except ZeroDivisionError:
            operator_2lt_coverage = 0

        worksheet.append(['ЭДО', 'Всего ИТС', 'С ЭДО', '%'])
        worksheet.append(['Охват ЭДО', len(all_its), len(edo_companies_count), edo_companies_coverage])
        if len(edo_companies_count) > 0:
            if len(operator_2ae) > 0:
                worksheet.append(['', '2AE', len(operator_2ae), operator_2ae_coverage])
            if len(operator_2ae_doki) > 0:
                worksheet.append(['', '2AE доки', len(operator_2ae_doki), operator_2ae_doki_coverage])
            if len(operator_2be) > 0:
                worksheet.append(['', '2BE', len(operator_2be), operator_2be_coverage])
            if len(operator_2bm) > 0:
                worksheet.append(['', '2BM', len(operator_2bm), operator_2bm_coverage])
            if len(operator_2al) > 0:
                worksheet.append(['', '2AL', len(operator_2al), operator_2al_coverage])
            if len(operator_2lb) > 0:
                worksheet.append(['', '2LB', len(operator_2lb), operator_2lb_coverage])
            if len(operator_2bk) > 0:
                worksheet.append(['', '2BK', len(operator_2bk), operator_2bk_coverage])
            if len(operator_2lt) > 0:
                worksheet.append(['', '2LT', len(operator_2lt), operator_2lt_coverage])
        worksheet.append(['Компании с трафиком больше 1', len(set(map(lambda x: x['Компания'], traffic_more_than_1)))])
        worksheet.append(['% активных ИТС', active_its_coverage])
        worksheet.append(['Сумма платного трафика', paid_traffic])
        worksheet.append([])

        #Сверка 2.0
        all_company = b.get_all('crm.company.list', {
                'select': ['UF_CRM_1735194029'],
                'filter': {
                    'ASSIGNED_BY_ID': user_info['ID'],
                }
            })
        company_sverka = list(filter(lambda x: x['UF_CRM_1735194029'] == '1', all_company))
        
        worksheet.append(['Сверка 2.0'])
        worksheet.append(['Подключено', len(company_sverka)])
        '''

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
        'MESSAGE': f'Отчет по пользователям сформирован. {upload_report["DETAIL_URL"]}'})
    os.remove(report_name)


if __name__ == '__main__':
    create_employees_report({
        'users': 'user_181'  #'user_129'   #'group_dr27', 'user_135'
    })
