from datetime import datetime, timedelta

from fast_bitrix24 import Bitrix

try:
    from authentication import authentication
    from field_values import deals_category_1_types
except ModuleNotFoundError:
    from web_app_4dk.modules.authentication import authentication
    from web_app_4dk.modules.field_values import deals_category_1_types


b = Bitrix(authentication('Bitrix'))
element_deal_type_codes = {
    'ИТС Земля': '2549',
    'СааС': '2551',
    'ИТС Земля + СааС': '2553',
    'ИТС Бесплатный': '2555',
    'Отчетность': '2557',
    'Отчетность (в рамках ИТС)': '2559',
    '1Спарк в договоре': '2561',
    '1Спарк 3000': '2563',
    '1СпаркПЛЮС 22500': '2565',
    '1С Контрагент': '2567',
    'ГРМ': '2569',
    'РПД': '2571',
    'Лицензия': '2573',
    '1С-Подпись': '2575',
    '1С-Подпись 1000': '2577',
    '1С Кабинет сотрудника': '2579',
    'Уникс': '2581',
    '1С Садовод': '2583',
    'ЭДО': '2585',
    'МДЛП': '2587',
    '1С Касса': '2589',
    'ЭТП': '2591',
    'Коннект': '2593',
    'Медицина': '2595',
    'Сервисное обслуживание': '2597',
    'Услуги': '2599',
    'Кабинет садовода': '2601',
    'ИТС Отраслевой': '2603',
    'ОФД': '2605',
    'Старт ЭДО': '2607',
    'Битрикс24': '2609',
    'Тестовый': '2611',
    'ПРОФ Земля': '2613',
    'ПРОФ Земля+Помощник': '2615',
    'ПРОФ Земля+Облако+Помощник': '2617',
    'ПРОФ Земля+Облако': '2619',
    'ПРОФ Облако': '2621',
    'ПРОФ Облако+Помощник': '2623',
    'Базовый Земля': '2625',
    'Базовый Облако': '2627',
    'Индивидуальный': '2629',
    'Индивидуальный+Облако': '2631',
    'Допы Облако': '2633',
    'Услуги (без нашего ИТС)': '2635',
    'АОВ': '2637',
    'АОВ+Облако': '2639',
    'ГРМ Спец': '2641',
    'ГРМ Бизнес': '2643',
    'Садовод+Помощник': '2645',
    'ДУО': '2647',
    'Лицензия с купоном ИТС': '2649',
}


def update_refusal_deal_element(req: dict):
    refusal_date = datetime.strptime(req['refusal_date'], '%d.%m.%Y')
    start_date_filter = (refusal_date - timedelta(days=180)).strftime('%Y-%m-%d')
    end_date_filter = (refusal_date + timedelta(days=1)).strftime('%Y-%m-%d')
    support_tasks = len(b.get_all('tasks.task.list', {
        'filter': {
            'GROUP_ID': '1',
            '>=CREATED_DATE': start_date_filter,
            '<CREATED_DATE': end_date_filter,
            'UF_CRM_TASK': ['CO_' + req['company_id']]
        }
    }))
    consultation_tasks = len(b.get_all('tasks.task.list', {
        'filter': {
            'GROUP_ID': '7',
            '>=CREATED_DATE': start_date_filter,
            '<CREATED_DATE': end_date_filter,
            'UF_CRM_TASK': ['CO_' + req['company_id']]
        }
    }))
    contacts_number = len(b.get_all('crm.company.contact.items.get', {'id': req['company_id']}))
    revenue_element = b.get_all('lists.element.get', {
        'IBLOCK_TYPE_ID': 'lists',
        'IBLOCK_ID': '257',
        'filter': {
            'PROPERTY_1631': req['company_id']
        }
    })[0]
    okved = list(revenue_element['PROPERTY_1629'].values())[0]
    employees_number = list(revenue_element['PROPERTY_1625'].values())[0]
    revenue = list(revenue_element['PROPERTY_1635'].values())[0]
    deal_type = b.get_all('crm.deal.get', {'ID': req['deal_id']})['TYPE_ID']
    element_deal_type_code = element_deal_type_codes[deals_category_1_types[deal_type]]
    element_info = b.get_all('lists.element.get', {
        'IBLOCK_TYPE_ID': 'lists',
        'IBLOCK_ID': '109',
        'ELEMENT_ID': req['element_id']
    })[0]

    b.call('lists.element.update', {
        'IBLOCK_TYPE_ID': 'lists',
        'IBLOCK_ID': '109',
        'ELEMENT_ID': req['element_id'],
        'fields': {
            'NAME': element_info['NAME'],
            'PROPERTY_519': list(element_info['PROPERTY_519'].values())[0],
            'PROPERTY_521': list(element_info['PROPERTY_521'].values())[0],
            'PROPERTY_523': list(element_info['PROPERTY_523'].values())[0],
            'PROPERTY_525': list(element_info['PROPERTY_525'].values())[0],
            'PROPERTY_527': list(element_info['PROPERTY_527'].values())[0],
            'PROPERTY_531': list(element_info['PROPERTY_531'].values())[0],
            'PROPERTY_533': list(element_info['PROPERTY_533'].values())[0],
            'PROPERTY_1311': list(element_info['PROPERTY_1311'].values())[0],
            'PROPERTY_1665': element_deal_type_code,
            'PROPERTY_1667': support_tasks,
            'PROPERTY_1669': consultation_tasks,
            'PROPERTY_1671': contacts_number,
            'PROPERTY_1673': okved,
            'PROPERTY_1675': revenue,
            'PROPERTY_1677': employees_number,
    }})
