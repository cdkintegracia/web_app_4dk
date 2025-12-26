from time import strftime
from time import time
from time import gmtime
from time import strptime
from datetime import timedelta

from web_app_4dk.tools import *



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
    '2023': '2241',
    '2024': '2755',
    '2025': '2757',
    '2026': '2759',
    '2027': '2761',
    '2028': '2763',
    '2029': '2765',
    '2030': '2767'
}


def sort_types(company_id):
    request_data = {
        'select': ['TYPE_ID'],
        'filter': {
            'COMPANY_ID': company_id,
            'CATEGORY_ID': '1',
            'STAGE_ID': [
                'C1:UC_0KJKTY',     # Счет сформирован
                'C1:UC_3J0IH6',     # Счет отправлен клиенту
                'C1:UC_KZSOR2',     # Нет оплаты
                'C1:UC_VQ5HJD',     # Ждём решения клиента
                'C1:NEW',           # Услуга активна
            ]
        }
    }
    deals = send_bitrix_request('crm.deal.list', request_data)
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
               '9',                                 # БизнесСтарт
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
               'UC_6TCS2E',                         # Линк
               '2',                                 # Контрагент (в договоре)
               ]
    type_element_codes = {
        'SALE': '2251',
        'COMPLEX': '2253',
        'UC_APUWEW': '2255',
        'UC_1UPOTU': '2257',
        'UC_O99QUW': '2259',
        'UC_OV4T7K': '2261',
        'UC_2B0CK2': '2263',
        'UC_86JXH1': '2265',
        'UC_WUGAZ7': '2267',
        'UC_A7G0AM': '2269',
        'GOODS': '2271',
        'UC_GZFC63': '2273',
        'UC_QQPYF0': '2275',
        'UC_8Z4N1O': '2277',
        'UC_FOKY52': '2279',
        'UC_D1DN7U': '2281',
        'UC_34QFP9': '2283',
        'UC_J426ZW': '2285',
        'UC_H8S037': '2287',
        'UC_8LW09Y': '2289',
        'UC_3SKJ5M': '2291',
        'UC_4B5UQD': '2293',
        'UC_H7HOD0': '2295',
        'UC_USDKKM': '2297',
        'SERVICE': '2299',
        'SERVICES': '2301',
        'UC_XJFZN4': '2303',
        'UC_BZYY0D': '2305',
        'UC_66Z1ZF': '2307',
        'UC_40Q6MC': '2309',
        'UC_74DPBQ': '2311',
        'UC_IV3HX1': '2313',
        'UC_HT9G9H': '2315',
        'UC_XIYCTV': '2317',
        'UC_5T4MAW': '2319',
        'UC_N113M9': '2321',
        'UC_ZKPT1B': '2323',
        'UC_2SJOEJ': '2325',
        'UC_AVBW73': '2327',
        'UC_GPT391': '2329',
        'UC_92H9MN': '2331',
        'UC_7V8HWF': '2333',
        'UC_IUJR81': '2335',
        'UC_2R01AE': '2337',
        'UC_81T8ZR': '2339',
        'UC_SV60SP': '2341',
        'UC_D7TC4I': '2343',
        'UC_K9QJDV': '2345',
        'UC_DBLSP5': '2347',
        'UC_GP5FR3': '2349',
        'UC_YIAJC8': '2351',
        '1': '2353',
        'UC_6TCS2E': '2357',
        '2': '2729',
        '9': '75373',
    }
    for type in level_1:
        if type in types:
            return type_element_codes[type]
    for type in level_2:
        if type in types:
            return type_element_codes[type]
    for type in level_3:
        if type in types:
            return type_element_codes[type]
    for type in level_4:
        if type in types:
            return type_element_codes[type]
    return '2355'


def create_element(company_id, outgoing_email=False, connect_treatment=False, call_duration=False, incoming_call=False, outgoing_call_other=False):
    current_date = f'{month_string[strftime("%m")]} {strftime("%Y")}'

    request_data = {
        'select': ['ASSIGNED_BY_ID'],
        'filter': {'ID': company_id}}
    responsible = send_bitrix_request('crm.company.list', request_data)[0]['ASSIGNED_BY_ID']

    lk_call_count = '0'
    string_call_duration = '00:00:00'
    if call_duration:
        lk_call_count = '1'
        string_call_duration = strftime("%H:%M:%S", call_duration)

    request_data = {
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
            'PROPERTY_1359': int(outgoing_email),  # Исходящие письма
            'PROPERTY_1361': '1',  # Всего взаимодействий
            'PROPERTY_1365': int(connect_treatment),  # Обращений в 1С:Коннект
            'PROPERTY_1369': int(incoming_call),   # Входящие звонки
            'PROPERTY_1375': int(outgoing_call_other),   # Исходящие (остальные)
            'PROPERTY_1377': sort_types(company_id)      # Топ сделка
        }
    }
    element = send_bitrix_request('lists.element.add', request_data)
    return str(element)


def rewrite_element(element_data, calls_duration, calls_count):
    property_1583 = calls_duration
    property_1585 = calls_count
    if 'PROPERTY_1303' not in element_data:
        property_1303 = '00:00:00'
    else:
        property_1303 = list(element_data['PROPERTY_1303'].values())[0]
    if 'PROPERTY_1305' not in element_data:
        property_1305 = '0'
    else:
        property_1305 = list(element_data['PROPERTY_1305'].values())[0]
    if 'PROPERTY_1307' not in element_data:
        property_1307 = '00:00:00'
    else:
        property_1307 = list(element_data['PROPERTY_1307'].values())[0]
    if 'PROPERTY_1315' not in element_data:
        property_1315 = ''
    else:
        property_1315 = list(element_data['PROPERTY_1315'].values())[0]
    if 'PROPERTY_1317' not in element_data:
        property_1317 = ''
    else:
        property_1317 = list(element_data['PROPERTY_1317'].values())[0]
    property_1299 = list(element_data['PROPERTY_1299'].values())[0]
    property_1339 = list(element_data['PROPERTY_1339'].values())[0]
    property_1341 = list(element_data['PROPERTY_1341'].values())[0]
    if 'PROPERTY_1355' not in element_data:
        property_1355 = ''
    else:
        property_1355 = list(element_data['PROPERTY_1355'].values())[0]
    if 'PROPERTY_1359' not in element_data:
        property_1359 = '0'
    else:
        property_1359 = list(element_data['PROPERTY_1359'].values())[0]
    if 'PROPERTY_1365' not in element_data:
        property_1365 = '0'
    else:
        property_1365 = list(element_data['PROPERTY_1365'].values())[0]
    if 'PROPERTY_1369' not in element_data:
        property_1369 = '0'
    else:
        property_1369 = list(element_data['PROPERTY_1369'].values())[0]
    if 'PROPERTY_1375' not in element_data:
        property_1375 = '0'
    else:
        property_1375 = list(element_data['PROPERTY_1375'].values())[0]
    if 'PROPERTY_1377' not in element_data:
        property_1377 = ''
    else:
        property_1377 = list(element_data['PROPERTY_1377'].values())[0]
    if 'PROPERTY_1663' not in element_data:
        property_1663 = ''
    else:
        property_1663 = list(element_data['PROPERTY_1663'].values())[0]
    property_1361 = int(property_1359) + int(property_1365) + int(property_1369) + int(property_1375) + int(property_1305)
    request_data = {
        'IBLOCK_TYPE_ID': 'lists',
        'IBLOCK_ID': '175',
        'ELEMENT_ID': element_data['ID'],
        'fields': {
            'NAME': element_data['NAME'],  # Название == месяц и год
            'PROPERTY_1299': property_1299,  # Привязка к компании
            'PROPERTY_1303': property_1303,  # Продолжительность звонка
            'PROPERTY_1305': property_1305,  # Количество звонков
            'PROPERTY_1307': property_1307,
            'PROPERTY_1315': property_1315,
            'PROPERTY_1317': property_1317,
            'PROPERTY_1339': property_1339,  # Месяц
            'PROPERTY_1341': property_1341,  # Год
            'PROPERTY_1355': property_1355,
            'PROPERTY_1359': property_1359,  # Исходящие письма
            'PROPERTY_1361': property_1361,  # Всего взаимодействий
            'PROPERTY_1365': property_1365,  # Обращений в 1С:Коннект
            'PROPERTY_1369': property_1369,  # Входящие звонки
            'PROPERTY_1375': property_1375,  # Исходящие (остальные)
            'PROPERTY_1377': property_1377,  # Топ сделка
            'PROPERTY_1583': property_1583,  # Продолжительность исх. зв. (Мегафон)
            'PROPERTY_1585': property_1585,  # Кол-во исх. зв. (Мегафон),
            'PROPERTY_1663': property_1663,
        }
    }
    element = send_bitrix_request('lists.element.update', request_data)


def update_element(company_id=None, element=None, outgoing_email=False, connect_treatment=False, call_duration=False, incoming_call=False, outgoing_call_other=False):
    lk_call_count = 0
    total_interactions_bool = True
    if call_duration:
        lk_call_count = 1
    if not element and company_id:
        current_date = f'{month_string[strftime("%m")]} {strftime("%Y")}'
        request_data = {
            'IBLOCK_TYPE_ID': 'lists',
            'IBLOCK_ID': '175',
            'filter': {
                'PROPERTY_1299': company_id,
                'NAME': current_date,
            }}
        element = send_bitrix_request('lists.element.get', request_data)
        if element:
            element = element[0]
        else:
            create_element(company_id)
            total_interactions_bool = False
            element = send_bitrix_request('lists.element.get', request_data)[0]
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
        request_data = {
            'select': ['ASSIGNED_BY_ID'],
            'filter': {'ID': company_id}}
        responsible = send_bitrix_request('crm.company.list', request_data)[0]['ASSIGNED_BY_ID']
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
    try:
        for field_value in element['PROPERTY_1375']:
            outgoing_calls_others = element['PROPERTY_1375'][field_value]
    except:
        outgoing_calls_others = '0'
    try:
        for field_value in element['PROPERTY_1663']:
            company_name = element['PROPERTY_1663'][field_value]
    except:
        company_name = ''

    # Форматирование времени в секунды и суммирование с длительностью звонка

    element_time = strptime(element_duration, "%H:%M:%S")
    element_seconds = timedelta(
        hours=element_time.tm_hour,
        minutes=element_time.tm_min,
        seconds=element_time.tm_sec
    ).seconds
    new_seconds = int(element_seconds) + int(call_duration)
    new_time = gmtime(new_seconds)

    request_data = {
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
            'PROPERTY_1361': str(int(total_interactions) + total_interactions_bool),  # Всего взаимодействий
            'PROPERTY_1365': str(int(connect_treatment_count) + connect_treatment),  # Обращений в 1С:Коннект
            'PROPERTY_1369': str(int(incoming_calls) + incoming_call),     # Входящие звонки
            'PROPERTY_1375': str(int(outgoing_calls_others) + outgoing_call_other),     # Исходящие (остальные)
            'PROPERTY_1377': top_deal,  # Топ сделка
            'PROPERTY_1663': company_name,
        }
    }
    send_bitrix_request('lists.element.update', request_data)

