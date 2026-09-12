from time import strftime
from time import time
from time import gmtime
from time import strptime
from datetime import timedelta





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
    deals = _api().pages('crm.deal.list', request_data)
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


# Общий модуль установлен отдельно (pip install из приложенного пакета).
if __package__:
    from .worklog_common import API, config, serialized, scalar, duration, hms, current_period, month_name
else:
    from worklog_common import API, config, serialized, scalar, duration, hms, current_period, month_name


def _api():
    return API(config())


def _increments(outgoing_email, connect_treatment, call_duration, incoming_call, outgoing_call_other):
    seconds = duration(call_duration)
    return seconds, {
        'PROPERTY_1305': int(bool(call_duration)),
        'PROPERTY_1359': int(outgoing_email),
        'PROPERTY_1365': int(connect_treatment),
        'PROPERTY_1369': int(incoming_call),
        'PROPERTY_1375': int(outgoing_call_other),
        'PROPERTY_1361': 1,
    }


@serialized
def create_element(company_id, outgoing_email=False, connect_treatment=False, call_duration=False, incoming_call=False, outgoing_call_other=False, responsible=None, period=None, count_interaction=True):
    api = _api()
    api.validate_fields()
    period = period or current_period(api.c)
    existing = api.find_element(company_id, period)
    if existing:
        if not count_interaction:
            return str(existing['ID'])
        update_element(company_id, existing, outgoing_email, connect_treatment,
                       call_duration, incoming_call, outgoing_call_other)
        return str(existing['ID'])
    seconds, increments = _increments(outgoing_email, connect_treatment,
                                      call_duration, incoming_call, outgoing_call_other)
    if not responsible:
        responsible = api.call('crm.company.get', {'id':company_id})['result']['ASSIGNED_BY_ID']
    if not count_interaction:
        increments['PROPERTY_1361'] = 0
    year, month = period.split('-')
    fields = {
        'NAME':month_name(period), 'PROPERTY_1299':company_id,
        'PROPERTY_1303':hms(seconds),
        'PROPERTY_1339':month_codes[month], 'PROPERTY_1341':year_codes[year],
        'PROPERTY_1355':responsible, 'PROPERTY_1377':sort_types(company_id),
    }
    fields.update({k:str(v) for k,v in increments.items()})
    fields.update(api.totals({},fields))
    # Тот же принцип создания, что в старом коде; тариф/лимит здесь не назначаем.
    result = api.call('lists.element.add',dict(api.list_params(),
        ELEMENT_CODE=f'company-{company_id}-{period}', FIELDS=fields),write=True)['result']
    return str(result)


@serialized
def rewrite_element(element_data, calls_duration, calls_count):
    api = _api()
    row = api.get_element(element_data['ID'])
    count_fields = ('PROPERTY_1359','PROPERTY_1365','PROPERTY_1369','PROPERTY_1375','PROPERTY_1305')
    changes = {'PROPERTY_1583':calls_duration, 'PROPERTY_1585':calls_count,
               'PROPERTY_1361':str(sum(int(scalar(row,k,'0') or 0) for k in count_fields))}
    return api.update_element(row, changes)


@serialized
def update_element(company_id=None, element=None, outgoing_email=False, connect_treatment=False, call_duration=False, incoming_call=False, outgoing_call_other=False):
    api = _api()
    if element:
        # Переданный вызывающим кодом снимок мог устареть: перечитываем под блокировкой.
        row = api.get_element(element['ID'])
    else:
        if not company_id:
            raise ValueError('Нужна компания или элемент списка')
        row = api.find_element(company_id,current_period(api.c))
        if row is None:
            return create_element(company_id,outgoing_email,connect_treatment,
                                  call_duration,incoming_call,outgoing_call_other)
    seconds, increments = _increments(outgoing_email,connect_treatment,
                                      call_duration,incoming_call,outgoing_call_other)
    changes = {k:str(int(scalar(row,k,'0') or 0)+v) for k,v in increments.items()}
    changes['PROPERTY_1303'] = hms(duration(scalar(row,'PROPERTY_1303'))+seconds)
    # Сохраняем поведение исходного обработчика для старых/неполных элементов.
    actual_company = scalar(row, 'PROPERTY_1299') or company_id
    if not actual_company:
        raise ValueError('У элемента не указана компания')
    if not scalar(row, 'PROPERTY_1355'):
        changes['PROPERTY_1355'] = api.call('crm.company.get', {
            'id': actual_company})['result']['ASSIGNED_BY_ID']
    # В исходнике читалось PROPERTY_1367, которого нет в схеме списка 175,
    # поэтому при обновлениях фактически вызывался sort_types(). Сохраняем этот расчёт.
    changes['PROPERTY_1377'] = sort_types(actual_company)
    if not scalar(row, 'PROPERTY_1315'):
        changes['PROPERTY_1315'] = '2207'  # Нет: первое превышение
    if not scalar(row, 'PROPERTY_1317'):
        changes['PROPERTY_1317'] = '2209'  # Нет: двойное превышение
    # Компания, месяц, год, лимит, признаки превышения и остальные поля сохраняются.
    return api.update_element(row,changes)
