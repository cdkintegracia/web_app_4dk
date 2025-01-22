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
    '+79219550056',     # Елена Захарчук
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
    '2023': '2241',
    '2024': '2755',
    '2025': '2757',
    '2027': '2759',
    '2028': '2761',
    '2029': '2763',
    '2030': '2765'
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

    #add_call(req)     # Запись в статистику пользователя
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

        if not list_elements:

            if req['data[CALL_TYPE]'] in ['2', '3']:
                create_element(company_id=company['COMPANY_ID'], incoming_call=True)

            elif req['data[CALL_TYPE]'] in ['1', ] and req['data[PORTAL_NUMBER]'] in employee_numbers:
                create_element(company_id=company['COMPANY_ID'], call_duration=call_duration)

            elif req['data[CALL_TYPE]'] == '1':
                create_element(company_id=company['COMPANY_ID'], outgoing_call_other=True)

        # Если найден элемент - он обновляется

        else:

            for element in list_elements:
                if req['data[CALL_TYPE]'] in ['2', '3']:
                    update_element(element=element, company_id=company['COMPANY_ID'], incoming_call=True)

                elif req['data[CALL_TYPE]'] in ['1', ] and req['data[PORTAL_NUMBER]'] in employee_numbers:
                    update_element(element=element, company_id=company['COMPANY_ID'], call_duration=call_duration_seconds)

                elif req['data[CALL_TYPE]'] == '1':
                    update_element(company_id=company['COMPANY_ID'], outgoing_call_other=True)



