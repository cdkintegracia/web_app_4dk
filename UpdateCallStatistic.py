from authentication import authentication
from fast_bitrix24 import Bitrix
from time import strftime


"""
call_types:
1 - входящий
2 - исходящий
"""

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
]

def update_call_statistic(client_number, employee_number):
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

    # Элементы списка

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
                'field': {
                    'NAME': current_date,
                    'PROPERTY_1297': '1',
                    'PROPERTY_1299': company['ID']
                }
            }
                   )