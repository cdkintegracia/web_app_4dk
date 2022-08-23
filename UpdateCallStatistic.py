from authentication import authentication
from fast_bitrix24 import Bitrix
from time import strftime
from time import time
from time import gmtime
from time import strptime
from datetime import timedelta

# Считывание файла authentication.txt

webhook = authentication('Bitrix')
b = Bitrix(webhook)

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

def update_call_statistic(req):
    if req['data[CALL_TYPE]'] not in ['1'] and req['data[PORTAL_NUMBER]'] not in employee_numbers and req['data[CALL_FAILED_CODE'] == '200':
        print('--------------------------------------------------')
        print(f'Неподходящий звонок {req["data[CALL_TYPE]"]} {req["data[PORTAL_NUMBER]"]}')
        print('--------------------------------------------------')
        return
    print('--------------------------------------------------')
    print(f'Подходящий звонок {req["data[CALL_TYPE]"]} {req["data[PORTAL_NUMBER]"]}')
    print(req)
    print('--------------------------------------------------')
    client_number = req['data[PHONE_NUMBER]']
    employee_number = req['data[PORTAL_NUMBER]']
    call_duration_seconds = req['data[CALL_DURATION]']
    call_duration = gmtime(int(req['data[CALL_DURATION]']))
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
    current_date = f'{month_string[strftime("%m")]} {strftime("%Y")}'

    # ID контакта через номер телефона

    contact = b.get_all('telephony.externalCall.searchCrmEntities', {'PHONE_NUMBER': client_number})
    contact_id = contact[0]['CRM_ENTITY_ID']

    # Компании, связанные с контактом | заполнение УС "Статистика звонков"

    companies = b.get_all('crm.contact.company.items.get', {'id': contact_id})
    for company in companies:
        list_elements = b.get_all('lists.element.get', {
            'IBLOCK_TYPE_ID': 'lists',
            'IBLOCK_ID': '175',
            'filter': {
                'PROPERTY_1299': company['COMPANY_ID'],
                'NAME': current_date,
            }
        }
                                  )

        # Если нет элемента списка для компании на текущую дату - создается новый элемент

        if len(list_elements) == 0:
            b.call('lists.element.add', {
                'IBLOCK_TYPE_ID': 'lists',
                'IBLOCK_ID': '175',
                'ELEMENT_CODE': time(),
                'fields': {
                    'NAME': current_date,
                    'PROPERTY_1303': strftime("%H:%M:%S", call_duration),
                    'PROPERTY_1299': company['COMPANY_ID'],
                    'PROPERTY_1305': '1'
                }
            }
                   )

        # Если найден элемент - он обновляется

        else:
            for element in list_elements:
                for field_value in element['PROPERTY_1303']:
                    element_duration = element['PROPERTY_1303'][field_value]
                for field_value in element['PROPERTY_1305']:
                    element_call_count = element['PROPERTY_1305'][field_value]

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
                    'PROPERTY_1303': strftime("%H:%M:%S", new_time),
                    'PROPERTY_1299': company['COMPANY_ID'],
                    'PROPERTY_1305': str(int(element_call_count) + 1)
                }
            }
                   )
