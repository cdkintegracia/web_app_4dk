from time import time

from fast_bitrix24 import Bitrix
import requests

try:
    from authentication import authentication
except ModuleNotFoundError:
    from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))
checko_url = 'https://api.checko.ru/v2/'
api_key = 'jMw7CIIIJtOKSNUb'
api_methods = ['entrepreneur', 'finances', 'company']
b24_list_element_fields = {
    'Выручка': 'PROPERTY_1621',
    'Среднесписочная численность': 'PROPERTY_1625',
    'ОКВЭД (Код)': 'PROPERTY_1627',
    'ОКВЭД (Наим)': 'PROPERTY_1629',
    'Компания': 'PROPERTY_1631',
    'Топ сделка': 'PROPERTY_1633',
    'Выручка в млн': 'PROPERTY_1635',
    'Дата регистрации': 'PROPERTY_1637',
    'Ответственный за компанию': 'PROPERTY_1639',
    'Год': 'PROPERTY_1643',
}


def create_request(method: str, parameters: list) -> str:
    return f"{checko_url}{method}?key={api_key}&{'&'.join(parameters)}"


def find_top_deal(company_id: str) -> str:
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
        # 'SALE': '2251',
        # 'COMPLEX': '2253',
        # 'UC_APUWEW': '2255',
        'UC_1UPOTU': '2405',
        'UC_O99QUW': '2407',
        'UC_OV4T7K': '2409',
        'UC_2B0CK2': '2411',
        'UC_86JXH1': '2413',
        'UC_WUGAZ7': '2415',
        'UC_A7G0AM': '2417',
        'GOODS': '2419',
        'UC_GZFC63': '2421',
        'UC_QQPYF0': '2423',
        'UC_8Z4N1O': '2425',
        'UC_FOKY52': '2427',
        'UC_D1DN7U': '2429',
        'UC_34QFP9': '2431',
        'UC_J426ZW': '2433',
        'UC_H8S037': '2435',
        'UC_8LW09Y': '2437',
        'UC_3SKJ5M': '2439',
        'UC_4B5UQD': '2441',
        'UC_H7HOD0': '2443',
        'UC_USDKKM': '2445',
        'SERVICE': '2447',
        'SERVICES': '2449',
        'UC_XJFZN4': '2451',
        'UC_BZYY0D': '2453',
        'UC_66Z1ZF': '2455',
        'UC_40Q6MC': '2457',
        'UC_74DPBQ': '2459',
        'UC_IV3HX1': '2461',
        'UC_HT9G9H': '2463',
        'UC_XIYCTV': '2465',
        'UC_5T4MAW': '2467',
        'UC_N113M9': '2469',
        'UC_ZKPT1B': '2471',
        'UC_2SJOEJ': '2473',
        'UC_AVBW73': '2475',
        'UC_GPT391': '2477',
        'UC_92H9MN': '2479',
        'UC_7V8HWF': '2481',
        'UC_IUJR81': '2483',
        'UC_2R01AE': '2485',
        'UC_81T8ZR': '2487',
        'UC_SV60SP': '2489',
        'UC_D7TC4I': '2491',
        'UC_K9QJDV': '2493',
        'UC_DBLSP5': '2495',
        'UC_GP5FR3': '2497',
        'UC_YIAJC8': '2499',
        '1': '2501',
        'UC_6TCS2E': '2505'
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
    return '2503'


def get_result_values(result: dict) -> dict:
    average_number_of_employees = -1
    OKVED_code = ''
    OKVED_name = ''
    registration_date = ''
    if 'СЧР' in result['data'] and result['data']['СЧР']:
        average_number_of_employees = result['data']['СЧР']
    if 'Код' in result['data']['ОКВЭД'] and result['data']['ОКВЭД']['Код']:
        OKVED_code = result['data']['ОКВЭД']['Код']
    if 'Наим' in result['data']['ОКВЭД'] and result['data']['ОКВЭД']['Наим']:
        OKVED_name = result['data']['ОКВЭД']['Наим']
    if 'ДатаРег' in result['data'] and result['data']['ДатаРег']:
        registration_date = result['data']['ДатаРег']

    return {
        'Среднесписочная численность': average_number_of_employees,
        'ОКВЭД (Код)': OKVED_code,
        'ОКВЭД (Наим)': OKVED_name,
        'Дата регистрации': registration_date
    }


def get_info_from_checko(req):
    year = req['year']
    errors = []
    b24_list_elements = b.get_all('lists.element.get', {
                    'IBLOCK_TYPE_ID': 'lists',
                    'IBLOCK_ID': '257',
                    'filter': {
                        'PROPERTY_1643': year,
                    }
    })
    b24_list_elements = list(map(lambda x: list(x['PROPERTY_1631'].values())[0], b24_list_elements))
    companies = b.get_all('crm.company.list', {
        'select': [
            'ID',
            'TITLE',
            'ASSIGNED_BY_ID',
            'UF_CRM_1656070716',     # СлужИНН
        ]})
    companies = list(filter(lambda x: x['ID'] not in b24_list_elements and x['UF_CRM_1656070716'], companies))
    count = 0
    for company_info in companies:
        print(count)
        if count == 499:
            break
        count += 1
        revenue = -1
        for method in api_methods:
            if method == 'entrepreneur' and len(company_info['UF_CRM_1656070716']) == 10:
                continue
            elif method != 'entrepreneur' and len(company_info['UF_CRM_1656070716']) != 10:
                continue
            checko_request = requests.get(url=create_request(method, [f"inn={company_info['UF_CRM_1656070716']}"]))
            if checko_request.status_code == 200:
                result = checko_request.json()
                if method == 'entrepreneur' and result['data']:
                    values = get_result_values(result)
                    b.call('lists.element.add', {
                        'IBLOCK_TYPE_ID': 'lists',
                        'IBLOCK_ID': '257',
                        'ELEMENT_CODE': time(),
                        'fields': {
                            'NAME': year,
                            b24_list_element_fields['ОКВЭД (Код)']: values['ОКВЭД (Код)'],
                            b24_list_element_fields['ОКВЭД (Наим)']: values['ОКВЭД (Наим)'],
                            b24_list_element_fields['Компания']: company_info['ID'],
                            b24_list_element_fields['Топ сделка']: find_top_deal(company_info['ID']),
                            b24_list_element_fields['Дата регистрации']: values['Дата регистрации'],
                            b24_list_element_fields['Ответственный за компанию']: company_info['ASSIGNED_BY_ID'],
                            b24_list_element_fields['Год']: year,
                        }
                    })
                    break
                elif method == 'finances':
                    if year in result['data'] and '2110' in result['data'][year]:
                        revenue = result['data'][year]['2110']
                elif method == 'company':
                    values = get_result_values(result)
                    b.call('lists.element.add', {
                        'IBLOCK_TYPE_ID': 'lists',
                        'IBLOCK_ID': '257',
                        'ELEMENT_CODE': time(),
                        'fields': {
                            'NAME': year,
                            b24_list_element_fields['Выручка']: revenue,
                            b24_list_element_fields['ОКВЭД (Код)']: values['ОКВЭД (Код)'],
                            b24_list_element_fields['ОКВЭД (Наим)']: values['ОКВЭД (Наим)'],
                            b24_list_element_fields['Среднесписочная численность']: values['Среднесписочная численность'],
                            b24_list_element_fields['Компания']: company_info['ID'],
                            b24_list_element_fields['Топ сделка']: find_top_deal(company_info['ID']),
                            b24_list_element_fields['Выручка в млн']: round(revenue / 1_000_000, 3),
                            b24_list_element_fields['Дата регистрации']: values['Дата регистрации'],
                            b24_list_element_fields['Ответственный за компанию']: company_info['ASSIGNED_BY_ID'],
                            b24_list_element_fields['Год']: year,

                        }
                    })

            else:
                errors.append(company_info['UF_CRM_1656070716'])
                break

    users_for_notifications = ['311', '1']
    if errors:
        count -= len(errors)
        notification_text = f'В УС "Выручка" было загружено {count} новых элементов\nНе удалось загрузить элементы для этих ИНН: {",".join(errors)}'
    else:
        notification_text = f'В УС "Выручка" было загружено {count} новых элементов'
    for user in users_for_notifications:
        b.call('im.notify.system.add', {
            'USER_ID': user,
            'MESSAGE': notification_text})


def update_elements(company_id: str):
    b24_list_elements = b.get_all('lists.element.get', {
        'IBLOCK_TYPE_ID': 'lists',
        'IBLOCK_ID': '257',
        'filter': {
            'PROPERTY_1631': company_id,
        }
    })
    for element in b24_list_elements:
        b.call('bizproc.workflow.start', {
            'TEMPLATE_ID': '1451',
            'DOCUMENT_ID': ['lists', 'Bitrix\Lists\BizprocDocumentLists', element['ID']]
        })


def create_revenue_list_elements(req: dict):
    if 'process' in req and req['process'] == 'update_elements':
        update_elements(req['company_id'])
    else:
        get_info_from_checko(req)


#get_info_from_checko({'year': '2021'})

