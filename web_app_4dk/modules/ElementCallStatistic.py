from time import strftime
from time import time
from time import gmtime
from time import strptime
from datetime import timedelta

from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication
from web_app_4dk.modules.UpdateUserStatistics import update_user_statistics

# Считывание файла authentication.txt

webhook = authentication('Bitrix')
b = Bitrix(webhook)


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

def sort_types(company_id):
    deals = b.get_all('crm.deal.list', {
        'select': ['TYPE_ID'],
        'filter': {
            'COMPANY_ID': company_id,
            'CATEGORY_ID': '1',
            'STAGE_ID': [
                'C1:UC_0KJKTY',     # Счет сформирован
                'C1:UC_3J0IH6',     # Счет отправлен клиенту
                'C1:UC_KZSOR2',     # Нет оплаты
                'C1:UC_VQ5HJD',     # Ждём решения клиента
                'C1:WON',           # Услуга завершена
            ]
        }
    })
    types = list(map(lambda x: x['TYPE_ID'], deals))
    level_1 = ['UC_HT9G9H',                         # ПРОФ Земля
               'UC_XIYCTV',                         # ПРОФ Земля+Помощник
               'UC_N113M9',                         # ПРОФ Земля+Облако
               'UC_5T4MAW',                         # ПРОФ Земля+Облако+Помощник
               'UC_ZKPT1B',                         # ПРОФ Облако
               'UC_2SJOEJ',                         # ПРОФ Облако+Помощник
               'UC_81T8ZR',                         # АОВ
               'UC_SV60SP',                         # АОВ+Облако
               'UC_92H9MN',                         # Индивидуальный
               'UC_7V8HWF',                         # Индивидуальный+Облако
               'UC_34QFP9',                         # Уникс
               ]
    level_2 = ['UC_AVBW73',                         # Базовый Земля
               'UC_GPT391',                         # Базовый Облако
               'UC_1UPOTU',                         # ИТС Бесплатный
               'UC_K9QJDV',                         # ГРМ Бизнес
               'GOODS',                             # ГРМ
               'UC_J426ZW',                         # Садовод
               'UC_DBLSP5',                         # Садовод+Помощник
               ]
    level_3 = ['UC_IUJR81',                         # Допы Облако
               'UC_USDKKM',                         # Медицина
               'UC_BZYY0D',                         # ИТС Отраслевой
               ]
    level_4 = ['UC_2R01AE',                         # Услуги (без нашего ИТС)
               'UC_IV3HX1',                         # Тестовый
               'UC_YIAJC8',                         # Лицензия с купоном ИТС
               'UC_QQPYF0',                         # Лицензия
               'UC_O99QUW',                         # Отчетность
               'UC_OV4T7K',                         # Отчетность (в рамках ИТС)
               'UC_2B0CK2',                         # 1Спарк в договоре
               'UC_86JXH1',                         # 1Спарк 3000
               'UC_WUGAZ7',                         # 1СпаркРиски ПЛЮС 22500
               'UC_A7G0AM',                         # Контрагент
               'UC_GZFC63',                         # РПД
               'UC_8Z4N1O',                         # Подпись
               'UC_FOKY52',                         # Подпись 1000
               'UC_D1DN7U',                         # Кабинет сотрудника
               'UC_H8S037',                         # ЭДО
               'UC_66Z1ZF',                         # ОФД
               'UC_40Q6MC',                         # СтартЭДО
               'UC_8LW09Y',                         # МДЛП
               'UC_3SKJ5M',                         # 1С Касса
               'UC_4B5UQD',                         # ЭТП
               'UC_H7HOD0',                         # Коннект
               'UC_XJFZN4',                         # Кабинет садовода
               'UC_74DPBQ',                         # БИТРИКС24
               ]
    type_names = {
        'SALE': 'ИТС Земля',
        'COMPLEX': 'СааС',
        'UC_APUWEW': 'ИТС Земля + СааС',
        'UC_1UPOTU': 'ИТС Бесплатный',
        'UC_O99QUW': 'Отчетность',
        'UC_OV4T7K': 'Отчетность (в рамках ИТС)',
        'UC_2B0CK2': '1Спарк в договоре',
        'UC_86JXH1': '1Спарк 3000',
        'UC_WUGAZ7': '1СпаркПЛЮС 22500',
        'UC_A7G0AM': '1С Контрагент',
        'GOODS': 'ГРМ',
        'UC_GZFC63': 'РПД',
        'UC_QQPYF0': 'Лицензия',
        'UC_8Z4N1O': '1С-Подпись',
        'UC_FOKY52': '1С-Подпись 1000',
        'UC_D1DN7U': '1С Кабинет сотрудника',
        'UC_34QFP9': 'Уникс',
        'UC_J426ZW': '1С Садовод',
        'UC_H8S037': 'ЭДО',
        'UC_8LW09Y': 'МДЛП',
        'UC_3SKJ5M': '1С Касса',
        'UC_4B5UQD': 'ЭТП',
        'UC_H7HOD0': 'Коннект',
        'UC_USDKKM': 'Медицина',
        'SERVICE': 'Сервисное обслуживание',
        'SERVICES': 'Услуги',
        'UC_XJFZN4': 'Кабинет садовода',
        'UC_BZYY0D': 'ИТС Отраслевой',
        'UC_66Z1ZF': 'ОФД',
        'UC_40Q6MC': 'Старт ЭДО',
        'UC_74DPBQ': 'Битрикс24',
        'UC_IV3HX1': 'Тестовый',
        'UC_HT9G9H': 'ПРОФ Земля',
        'UC_XIYCTV': 'ПРОФ Земля+Помощник',
        'UC_5T4MAW': 'ПРОФ Земля+Облако+Помощник',
        'UC_N113M9': 'ПРОФ Земля+Облако',
        'UC_ZKPT1B': 'ПРОФ Облако',
        'UC_2SJOEJ': 'ПРОФ Облако+Помощник',
        'UC_AVBW73': 'Базовый Земля',
        'UC_GPT391': 'Базовый Облако',
        'UC_92H9MN': 'Индивидуальный',
        'UC_7V8HWF': 'Индивидуальный+Облако',
        'UC_IUJR81': 'Допы Облако',
        'UC_2R01AE': 'Услуги (без нашего ИТС)',
        'UC_81T8ZR': 'АОВ',
        'UC_SV60SP': 'АОВ+Облако',
        'UC_D7TC4I': 'ГРМ Спец',
        'UC_K9QJDV': 'ГРМ Бизнес',
        'UC_DBLSP5': 'Садовод+Помощник',
        'UC_GP5FR3': 'ДУО',
        'UC_YIAJC8': 'Лицензия с купоном ИТС',
        '1': 'Не указан',
    }
    for type in level_1:
        if type in types:
            return type_names[type]
    for type in level_2:
        if type in types:
            return type_names[type]
    for type in level_3:
        if type in types:
            return type_names[type]
    for type in level_4:
        if type in types:
            return type_names[type]
    return 'Не найден'


def create_element(company_id, call_duration=None):
    current_date = f'{month_string[strftime("%m")]} {strftime("%Y")}'

    responsible = b.get_all('crm.company.list', {
        'select': ['ASSIGNED_BY_ID'],
        'filter': {'ID': company_id}})[0]['ASSIGNED_BY_ID']

    lk_call_count = '0'
    total_interactions = '0'
    string_call_duration = '00:00:00'
    if call_duration:
        lk_call_count = '1'
        string_call_duration = strftime("%H:%M:%S", call_duration)
        total_interactions = '1'

    b.call('lists.element.add', {
        'IBLOCK_TYPE_ID': 'lists',
        'IBLOCK_ID': '175',
        'ELEMENT_CODE': time(),
        'fields': {
            'NAME': current_date,  # Название == месяц и год
            'PROPERTY_1303': string_call_duration,  # Продолжительность звонка
            'PROPERTY_1299': company_id,  # Привязка к компании
            'PROPERTY_1305': str(lk_call_count),  # Количество звонков
            'PROPERTY_1339': month_codes[strftime("%m")],  # Месяц
            'PROPERTY_1341': year_codes[strftime('%Y')],  # Год
            'PROPERTY_1355': responsible,
            'PROPERTY_1359': '0',  # Исходящие письма
            'PROPERTY_1361': total_interactions,  # Всего взаимодействий
            'PROPERTY_1365': '0',  # Обращений в 1С:Коннект
            'PROPERTY_1367': sort_types(company_id),  # Топ сделка
            'PROPERTY_1369': '0',   # Входящие звонки
        }
    }
           )


def update_element(company_id=None, element=None, outgoing_email=False, connect_treatment=False, call_duration_seconds=False, incoming_call=False):
    lk_call_count = 0
    if call_duration_seconds:
        lk_call_count = 1
    if not element and company_id:
        current_date = f'{month_string[strftime("%m")]} {strftime("%Y")}'
        element = b.get_all('lists.element.get', {
            'IBLOCK_TYPE_ID': 'lists',
            'IBLOCK_ID': '175',
            'filter': {
                'PROPERTY_1299': company_id,
                'NAME': current_date,
            }})
    if not element:
        return
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
            'filter': {'ID': company_id}})[0]['ASSIGNED_BY_ID']
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
        top_deal = sort_types(company_id)
    try:
        for field_value in element['PROPERTY_1369']:
            incoming_calls = element['PROPERTY_1369'][field_value]
    except:
        incoming_calls = '0'

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
            'PROPERTY_1303': strftime("%H:%M:%S", new_time),  # Продолжительность звонков
            'PROPERTY_1299': company_id,  # Привязка к компании
            'PROPERTY_1305': str(int(element_call_count) + lk_call_count),  # Количество звонков
            'PROPERTY_1307': limit_duration,  # Лимит продолжительности звонков
            'PROPERTY_1315': first_break_limit,  # Превышение лимита
            'PROPERTY_1317': second_break_limit,  # Превышение лимита x2
            'PROPERTY_1339': month_codes[strftime("%m")],  # Месяц
            'PROPERTY_1341': year_codes[strftime('%Y')],  # Год
            'PROPERTY_1355': responsible,
            'PROPERTY_1359': str(int(sent_emails) + outgoing_email),  # Исходящие письма
            'PROPERTY_1361': str(int(total_interactions) + 1),  # Всегда взаимодействий
            'PROPERTY_1365': str(int(connect_treatment_count) + connect_treatment),  # Обращений в 1С:Коннект
            'PROPERTY_1367': top_deal,  # Топ сделка
            'PROPERTY_1369': str(int(incoming_calls) + int(incoming_call)),     # Входящие звонки
        }
    }
           )
