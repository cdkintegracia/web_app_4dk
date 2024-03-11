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
    #quarter_start_filter = datetime(day=1, month=quarter[0], year=datetime.now().year)
    month_end = quarter[-1] + 1
    year_end=datetime.now().year
    if month_end == 13:
        month_end = 1
        year_end = year_end + 1
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
        start_year_deals_data = read_deals_data_file(12, report_year-1)
        quarter_deals_data = read_deals_data_file(get_quarter_filter(report_month)['start_date'].month, report_year)
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
                                                   x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту']
                                                   , last_month_deals_data))

        spark_in_contract_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                         '1Спарк в договоре' == x['Тип'] and
                                                         x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                         last_month_deals_data))
        # 2024-01-20
        #spark_3000_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
        #                                          '1Спарк 3000' == x['Тип'] and
        #                                          x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
        #                                          last_month_deals_data))


        spark_3000_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                  ('1Спарк 3000' == x['Тип'] or '1Спарк' == x['Тип']) and
                                                  x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                  last_month_deals_data))

        # 2024-01-20
        #spark_22500_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
        #                                           '22500' in x['Тип'] and
        #                                           x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
        #                                           last_month_deals_data))


        spark_22500_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                                   ('22500' in x['Тип'] or '1СпаркПЛЮС' in x['Тип']) and
                                                   x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                   last_month_deals_data))

        rpd_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
                                           'РПД' in x['Тип'] and
                                           x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                           last_month_deals_data))

        other_deals_last_month = list(filter(lambda x: x['Ответственный'] == user_name and
                                             x not in its_prof_deals_last_month and
                                             x not in its_base_deals_last_month and
                                             x not in countragent_deals_last_month and
                                             x not in spark_in_contract_deals_last_month and
                                             x not in spark_3000_deals_last_month and
                                             x not in spark_22500_deals_last_month and
                                             x not in rpd_deals_last_month and
                                             x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'], last_month_deals_data))

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

        #2024-01-20
        #spark_3000_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
        #                                                 '1Спарк 3000' == x['Тип'] and
        #                                                 x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
        #                                                 before_last_month_deals_data))

        #spark_22500_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
        #                                                  '22500' in x['Тип'] and
        #                                                  x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
        #                                                  before_last_month_deals_data))

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

        other_deals_before_last_month = list(filter(lambda x: x['Ответственный'] == user_name and
                                                    x not in its_prof_deals_before_last_month and
                                                    x not in its_base_deals_before_last_month and
                                                    x not in countragent_deals_before_last_month and
                                                    x not in spark_in_contract_deals_before_last_month and
                                                    x not in spark_3000_deals_before_last_month and
                                                    x not in spark_22500_deals_before_last_month and
                                                    x not in rpd_deals_before_last_month and
                                                    x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                                    before_last_month_deals_data))

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

        #2024-01-20
        #spark_3000_deals_quarter = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
        #                                       '1Спарк 3000' == x['Тип'] and
        #                                       x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
        #                                       quarter_deals_data))

        #spark_22500_deals_quarter = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
        #                                        '22500' in x['Тип'] and
        #                                        x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
        #                                        quarter_deals_data))
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

        other_deals_quarter = list(filter(lambda x: x['Ответственный'] == user_name and
                                          x not in its_prof_deals_quarter and
                                          x not in its_base_deals_quarter and
                                          x not in countragent_deals_quarter and
                                          x not in spark_in_contract_deals_quarter and
                                          x not in spark_3000_deals_quarter and
                                          x not in spark_22500_deals_quarter and
                                          x not in rpd_deals_quarter and
                                          x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                          quarter_deals_data))

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

        #2024-01-20
        #spark_3000_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
        #                                          '1Спарк 3000' == x['Тип'] and
        #                                          x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
        #                                          start_year_deals_data))

        #spark_22500_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and x['Тип'] and
        #                                           '22500' in x['Тип'] and
        #                                           x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
        #                                           start_year_deals_data))
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

        other_deals_start_year = list(filter(lambda x: x['Ответственный'] == user_name and
                                             x not in its_prof_deals_start_year and
                                             x not in its_base_deals_start_year and
                                             x not in countragent_deals_start_year and
                                             x not in spark_in_contract_deals_start_year and
                                             x not in spark_3000_deals_start_year and
                                             x not in spark_22500_deals_start_year and
                                             x not in rpd_deals_start_year and
                                             x['Стадия сделки'] in ['Услуга активна', 'Счет сформирован', 'Счет отправлен клиенту'],
                                             start_year_deals_data))

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
            'Остальные',
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
            filter(lambda x: x['Ответственный за компанию'] == user_info['ID'], before_last_month_deals_data))))
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
            filter(lambda x: x['Ответственный за компанию'] == user_info['ID'], start_year_deals_data))))
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

        paid_reporting_deals_last_month = 0
        for its_deal in its_deals_last_month:
            its_paid_reporting = list(filter(lambda x: (x['Регномер'] == its_deal['Регномер'] and x['Тип'] == 'Отчетность') or
                                                       (x['Компания'] == its_deal['Компания'] and x['Тип'] == 'Отчетность'), last_month_deals_data))
            if its_paid_reporting:
                paid_reporting_deals_last_month += 1

        try:
            coverage_paid_reporting_deals_last_month = round(round(paid_reporting_deals_last_month /
                                                             len(its_deals_last_month), 2) * 100, 2)
        except ZeroDivisionError:
            coverage_paid_reporting_deals_last_month = 0

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
        for its_deal in its_deals_before_last_month:
            its_paid_reporting = list(
                filter(lambda x: (x['Регномер'] == its_deal['Регномер'] and x['Тип'] == 'Отчетность') or
                                 (x['Компания'] == its_deal['Компания'] and x['Тип'] == 'Отчетность'),
                       before_last_month_deals_data))
            if its_paid_reporting:
                paid_reporting_deals_before_last_month += 1

        try:
            coverage_paid_reporting_deals_before_last_month = round(round(paid_reporting_deals_before_last_month /
                                                                    len(its_deals_before_last_month), 2) * 100, 2)
        except ZeroDivisionError:
            coverage_paid_reporting_deals_before_last_month = 0

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
        for its_deal in its_deals_start_year:
            its_paid_reporting = list(
                filter(lambda x: (x['Регномер'] == its_deal['Регномер'] and x['Тип'] == 'Отчетность') or
                                 (x['Компания'] == its_deal['Компания'] and x['Тип'] == 'Отчетность'),
                       start_year_deals_data))
            if its_paid_reporting:
                paid_reporting_deals_start_year += 1

        try:
            coverage_paid_reporting_deals_start_year = round(round(paid_reporting_deals_start_year /
                                                             len(its_deals_start_year), 2) * 100, 2)
        except ZeroDivisionError:
            coverage_paid_reporting_deals_start_year = 0



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
        worksheet.append([
            'Платных отчетностей',
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
        if sales:
            sold_deals = b.get_all('crm.deal.list', {
                'select': ['UF_CRM_1657878818384', 'OPPORTUNITY', 'TYPE_ID'],
                'filter': {
                    'ID': list(map(lambda x: x['parentId2'], sales))
                }
            })
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
                'select': ['UF_CRM_1638093692254'],
                'filter': {
                    'ID': list(map(lambda x: x['Компания'], list(filter(lambda y: 'Компания' in y and y['Компания'], all_its))))
                }
            })
            edo_companies_count = list(filter(lambda x: x['UF_CRM_1638093692254'] == '69', edo_companies))
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

        try:
            edo_companies_coverage = round((len(edo_companies_count) / len(all_its)) * 100, 2)
        except ZeroDivisionError:
            edo_companies_coverage = 0

        try:
            active_its_coverage = round((len(traffic_more_than_1) / len(all_its)) * 100, 2)
        except ZeroDivisionError:
            active_its_coverage = 0

        worksheet.append(['ЭДО', 'Всего ИТС', 'С ЭДО', '%'])
        worksheet.append(['Охват ЭДО', len(all_its), len(edo_companies_count), edo_companies_coverage])
        worksheet.append(['Компании с трафиком больше 1', len(set(map(lambda x: x['Компания'], traffic_more_than_1)))])
        worksheet.append(['% активных ИТС', active_its_coverage])
        worksheet.append(['Сумма платного трафика', paid_traffic])

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
