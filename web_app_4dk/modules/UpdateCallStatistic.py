from time import strftime
from time import gmtime

from web_app_4dk.modules.UpdateUserStatistics import add_call
from web_app_4dk.modules.ElementCallStatistic import update_element, create_element
from web_app_4dk.tools import *


employee_numbers = [
    '+79991174816',     # Жанна Умалатова
    '+79991174814',     # Елена Коршакова
    '+79991174815',     # Екатерина Плотникова
    '+79991174818',     # Ольга Цветкова
    '+79991174812',     # Мария Боцула
    '+79522806626',     # МОЙ
    '+79991174813',     # Любовь Корсунова
    '+79991174826',     # Борис
]

month_codes = {
    '01': '2215',
    '02': '2217',
    '03': '2219',
    '04': '2221',
    '05': '2223',
    '06': '2225',
    '07': '2227',
    '08': '2229',
    '09': '2231',
    '10': '2233',
    '11': '2235',
    '12': '2237'
}

year_codes = {
    '2022': '2239',
    '2023': '2241'
}

month_string = {
        '01': 'Январь',
        '02': 'Февраль',
        '03': 'Март',
        '04': 'Апрель',
        '05': 'Май',
        '06': 'Июнь',
        '07': 'Июль',
        '08': 'Август',
        '09': 'Сентябрь',
        '10': 'Октябрь',
        '11': 'Ноябрь',
        '12': 'Декабрь'
    }

request_data = {'filter': {'UF_DEPARTMENT': ['231', ]}}
allowed_departments = send_bitrix_request('user.get', request_data)
allowed_numbers = []
for employee in allowed_departments:
    allowed_numbers.append(employee['WORK_PHONE'])


def update_call_statistic(req):
    """
    :param req: request.form
    :return: Обновление или создание элемента в УС "Статистика звонков"
    """

    add_call(req)     # Запись в статистику пользователя
    if req['data[CALL_FAILED_CODE]'] != '200':
        return

    client_number = req['data[PHONE_NUMBER]']
    call_duration_seconds = req['data[CALL_DURATION]']
    call_duration = gmtime(int(req['data[CALL_DURATION]']))
    current_date = f'{month_string[strftime("%m")]} {strftime("%Y")}'

    # ID контакта через номер телефона

    request_data = {'PHONE_NUMBER': client_number}
    contact = send_bitrix_request('telephony.externalCall.searchCrmEntities', request_data)
    if not contact:
        return
    contact_id = contact[0]['CRM_ENTITY_ID']

    # Компании, связанные с контактом | заполнение УС "Статистика звонков"

    request_data = {'id': contact_id}
    companies = send_bitrix_request('crm.contact.company.items.get', request_data)
    for company in companies:
        request_data = {
            'IBLOCK_TYPE_ID': 'lists',
            'IBLOCK_ID': '175',
            'filter': {
                'PROPERTY_1299': company['COMPANY_ID'],
                'NAME': current_date,
            }
        }
        list_elements = send_bitrix_request('lists.element.get', request_data)

        # Если нет элемента списка для компании на текущую дату - создается новый элемент

        if len(list_elements) == 0:

            if req['data[CALL_TYPE]'] in ['2', '3']:
                create_element(company_id=company['COMPANY_ID'], incoming_call=True)

            elif req['data[CALL_TYPE]'] in ['1', ] and req['data[PORTAL_NUMBER]'] in employee_numbers:
                create_element(company_id=company['COMPANY_ID'], call_duration=call_duration)

            elif req['data[CALL_TYPE]'] == '1':
                create_element(company_id=company['COMPANY_ID'], outgoing_call_other=True)

            '''
            responsible = b.get_all('crm.company.list', {
                'select': ['ASSIGNED_BY_ID'],
                'filter': {'ID': company['COMPANY_ID']}})[0]['ASSIGNED_BY_ID']
            b.call('lists.element.add', {
                'IBLOCK_TYPE_ID': 'lists',
                'IBLOCK_ID': '175',
                'ELEMENT_CODE': time(),
                'fields': {
                    'NAME': current_date,   # Название == месяц и год
                    'PROPERTY_1303': strftime("%H:%M:%S", call_duration),   # Продолжительность звонка
                    'PROPERTY_1299': company['COMPANY_ID'],     # Привязка к компании
                    'PROPERTY_1305': '1',    # Количество звонков
                    'PROPERTY_1339': month_codes[strftime("%m")],  # Месяц
                    'PROPERTY_1341': year_codes[strftime('%Y')],  # Год
                    'PROPERTY_1355': responsible,
                    'PROPERTY_1359': '0',   # Исходящие письма
                    'PROPERTY_1361': 1,     # Всего взаимодействий
                    'PROPERTY_1365': '0',  # Обращений в 1С:Коннект
                    'PROPERTY_1367': sort_types(company['COMPANY_ID']),     # Топ сделка
                }
            }
                   )
            '''

        # Если найден элемент - он обновляется

        else:

            for element in list_elements:
                if req['data[CALL_TYPE]'] in ['2', '3']:
                    update_element(element=element, company_id=company['COMPANY_ID'], incoming_call=True)

                elif req['data[CALL_TYPE]'] in ['1', ] and req['data[PORTAL_NUMBER]'] in employee_numbers:
                    update_element(element=element, company_id=company['COMPANY_ID'], call_duration=call_duration_seconds)

                elif req['data[CALL_TYPE]'] == '1':
                    update_element(company_id=company['COMPANY_ID'], outgoing_call_other=True)
                '''
                for field_value in element['PROPERTY_1303']:
                    element_duration = element['PROPERTY_1303'][field_value]
                for field_value in element['PROPERTY_1305']:
                    element_call_count = element['PROPERTY_1305'][field_value]
                for field_value in element['PROPERTY_1307']:
                    limit_duration = element['PROPERTY_1307'][field_value]
                if 'PROPERTY_1355' in element:
                    for field_value in element['PROPERTY_1355']:
                        responsible = element['PROPERTY_1355'][field_value]
                else:
                    responsible = b.get_all('crm.company.list', {
                        'select': ['ASSIGNED_BY_ID'],
                        'filter': {'ID': company['COMPANY_ID']}})[0]['ASSIGNED_BY_ID']
                try:
                    for field_value in element['PROPERTY_1315']:
                        first_break_limit = element['PROPERTY_1315'][field_value]
                except:
                    first_break_limit = '2207'
                try:
                    for field_value in element['PROPERTY_1317']:
                        second_break_limit = element['PROPERTY_1317'][field_value]
                except:
                    second_break_limit = '2209'
                try:
                    for field_value in element['PROPERTY_1359']:
                        sent_emails = element['PROPERTY_1359'][field_value]
                except:
                    sent_emails = '0'
                try:
                    for field_value in element['PROPERTY_1361']:
                        total_interactions = element['PROPERTY_1361'][field_value]
                except:
                    total_interactions = '0'
                try:
                    for field_value in element['PROPERTY_1365']:
                        connect_treatment_count = element['PROPERTY_1365'][field_value]
                except:
                    connect_treatment_count = '0'
                try:
                    for field_value in element['PROPERTY_1367']:
                        top_deal = element['PROPERTY_1367'][field_value]
                except:
                    top_deal = sort_types(company['COMPANY_ID'])

            # Форматирование времени в секунды и суммирование с длительностью звонка

            element_time = strptime(element_duration, "%H:%M:%S")
            element_seconds = timedelta(
                hours=element_time.tm_hour,
                minutes=element_time.tm_min,
                seconds=element_time.tm_sec
            ).seconds
            new_seconds = int(element_seconds) + int(call_duration_seconds)
            new_time = gmtime(new_seconds)

            b.call('lists.element.update', {
                'IBLOCK_TYPE_ID': 'lists',
                'IBLOCK_ID': '175',
                'ELEMENT_ID': element['ID'],
                'fields': {
                    'NAME': element['NAME'],
                    'PROPERTY_1303': strftime("%H:%M:%S", new_time),    # Продолжительность звонков
                    'PROPERTY_1299': company['COMPANY_ID'],     # Привязка к компании
                    'PROPERTY_1305': str(int(element_call_count) + 1),   # Количество звонков
                    'PROPERTY_1307': limit_duration,    # Лимит продолжительности звонков
                    'PROPERTY_1315': first_break_limit,     # Превышение лимита
                    'PROPERTY_1317': second_break_limit,    # Превышение лимита x2
                    'PROPERTY_1339': month_codes[strftime("%m")],   # Месяц
                    'PROPERTY_1341': year_codes[strftime('%Y')],    # Год
                    'PROPERTY_1355': responsible,
                    'PROPERTY_1359': sent_emails,     # Исходящие письма
                    'PROPERTY_1361': str(int(total_interactions) + 1),  # Всегда взаимодействий
                    'PROPERTY_1365': connect_treatment_count,           # Обращений в 1С:Коннект
                    'PROPERTY_1367': top_deal,                          # Топ сделка
                }
            }
                   )
            '''

