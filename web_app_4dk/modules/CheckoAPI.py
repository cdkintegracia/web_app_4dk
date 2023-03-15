from time import time

from fast_bitrix24 import Bitrix
import requests

from authentication import authentication


b = Bitrix(authentication('Bitrix'))
checko_url = 'https://api.checko.ru/v2/'
api_key = 'eF5kqvvyrN2eqCaU'
api_methods = ['entrepreneur', 'finances', 'company']
b24_list_element_fields = {
    'Выручка 2021': 'PROPERTY_1621',
    'Выручка 2022': 'PROPERTY_1623',
    'Среднесписочная численность': 'PROPERTY_1625',
    'ОКВЭД (Код)': 'PROPERTY_1627',
    'ОКВЭД (Наим)': 'PROPERTY_1629',
    'Компания': 'PROPERTY_1631',
    'Топ сделка': 'PROPERTY_1633',
}


def create_request(method:str, parameters:list) -> str:
    return f"{checko_url}{method}?key={api_key}&{'&'.join(parameters)}"


def find_top_deal(company_id):
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
    deals = b.get_all('crm.deal.list', request_data)
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
               'UC_6TCS2E',                         # Линк
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
        'UC_6TCS2E': '2357'
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


def get_info_from_checko():
    errors = []
    inn = '7813291736'
    company_id = '549'
    company_name = 'АСБО 7813291736'
    for method in api_methods:
        checko_request = requests.get(url=create_request(method, [f'inn={inn}']))
        if checko_request.status_code == 200:
            result = checko_request.json()
            revenue_2021 = -1
            average_number_of_employees = -1
            if method == 'entrepreneur' and result['data']:
                b.call('lists.element.add', {
                    'IBLOCK_TYPE_ID': 'lists',
                    'IBLOCK_ID': '257',
                    'ELEMENT_CODE': time(),
                    'fields': {
                        'NAME': company_name,
                        b24_list_element_fields['ОКВЭД (Код)']: result['data']['ОКВЭД']['Код'],
                        b24_list_element_fields['ОКВЭД (Наим)']: result['data']['ОКВЭД']['Наим'],
                        b24_list_element_fields['Компания']: company_id,
                    }
                })
                break
            elif method == 'finances':
                if '2021' in result['data'] and '2110' in result['data']['2021']:
                    revenue_2021 = result['data']['2021']['2110']
            elif method == 'company':
                if result['data']['СЧР']:
                    average_number_of_employees = result['data']['СЧР']
                b.call('lists.element.add', {
                    'IBLOCK_TYPE_ID': 'lists',
                    'IBLOCK_ID': '257',
                    'ELEMENT_CODE': time(),
                    'fields': {
                        'NAME': company_name,
                        b24_list_element_fields['Выручка 2021']: revenue_2021,
                        b24_list_element_fields['ОКВЭД (Код)']: result['data']['ОКВЭД']['Код'],
                        b24_list_element_fields['ОКВЭД (Наим)']: result['data']['ОКВЭД']['Наим'],
                        b24_list_element_fields['Среднесписочная численность']: average_number_of_employees,
                        b24_list_element_fields['Компания']: company_id,
                    }
                })

        else:
            errors.append(inn)
    print(errors)


def test():
    a = b.get_all('lists.element.get', {
                    'IBLOCK_TYPE_ID': 'lists',
                    'IBLOCK_ID': '257',
                    'ELEMENT_ID': '405841'})
    print(a)
#test()
exit()
#get_info_from_checko()


