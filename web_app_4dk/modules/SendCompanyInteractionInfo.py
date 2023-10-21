from datetime import datetime, timedelta
from calendar import monthrange
from time import sleep

from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication

b = Bitrix(authentication('Bitrix'))


def send_company_interaction_info(req):
    current_day = datetime.now().day
    current_day = 31
    month_day_range = monthrange(datetime.now().year, datetime.now().month)[1]
    task_deadline_date = datetime.now() + timedelta(days=1)
    if task_deadline_date.isoweekday() == 6:
        task_deadline_date += timedelta(days=2)
    elif task_deadline_date.isoweekday() == 7:
        task_deadline_date += timedelta(days=1)
    if current_day != month_day_range:
        return
    month_int_names = {
        1: 'Январь',
        2: 'Февраль',
        3: 'Март',
        4: 'Апрель',
        5: 'Май',
        6: 'Июнь',
        7: 'Июль',
        8: 'Август',
        9: 'Сентябрь',
        10: 'Октябрь',
        11: 'Ноябрь',
        12: 'Декабрь',
    }
    filter_month = datetime.now().month + 1
    filter_year = datetime.now().year
    filter_dates = []
    for _ in range(3):
        filter_month -= 1
        if filter_month == 0:
            filter_month = 12
            filter_year -= 1
        filter_dates.append(f"{month_int_names[filter_month]} {filter_year}")
    companies = b.get_all('crm.company.list', {'select': ['TITLE']})
    its_deals = b.get_all('crm.deal.list', {
        'select': ['ASSIGNED_BY_ID', 'COMPANY_ID'],
        'filter': {
            'UF_CRM_1657878818384': '859',
            'STAGE_ID': ['C1:NEW', 'C1:UC_0KJKTY', 'C1:UC_3J0IH6', 'C1:UC_KZSOR2', 'C1:UC_VQ5HJD']
        }})
    companies_interaction_info = b.get_all('lists.element.get', {
        'IBLOCK_TYPE_ID': 'lists',
        'IBLOCK_ID': '175',
        'filter': {
            'NAME': filter_dates,
            'PROPERTY_1361': '0',
        }
    })
    companies_top_deal = {}
    element_deal_type_name = {
        '2315': 'ПРОФ Земля',
        '2317': 'ПРОФ Земля+Помощник',
        '2321': 'ПРОФ Земля+Облако',
        '2319': 'ПРОФ Земля+Облако+Помощник',
        '2323': 'ПРОФ Облако',
        '2325': 'ПРОФ Облако+Помощник',
        '2339': 'АОВ',
        '2341': 'АОВ+Облако',
        '2331': 'Индивидуальный',
        '2333': 'Индивидуальный+Облако',
        '2283': 'Уникс',
        '2327': 'Базовый Земля',
        '2329': 'Базовый Облако',
        '2257': 'ИТС Бесплатный',
        '2345': 'ГРМ Бизнес',
        '2271': 'ГРМ',
        '2285': 'Садовод',
        '2347': 'Садовод+Помощник',
        '2335': 'Допы Облако',
        '2297': 'Медицина',
        '2305': 'ИТС Отраслевой',
        '2337': 'Услуги (без нашего ИТС)',
        '2313': 'Тестовый',
        '2351': 'Лицензия с купоном ИТС',
        '2275': 'Лицензия',
        '2259': 'Отчетность',
        '2261': 'Отчетность (в рамках ИТС)',
        '2263': '1Спарк в договоре',
        '2265': '1Спарк 3000',
        '2267': '1СпаркРиски ПЛЮС 22500',
        '2269': 'Контрагент',
        '2273': 'РПД',
        '2277': 'Подпись',
        '2279': 'Подпись 1000',
        '2281': 'Кабинет сотрудника',
        '2287': 'ЭДО',
        '2307': 'ОФД',
        '2309': 'СтартЭДО',
        '2289': 'МДЛП',
        '2291': '1С Касса',
        '2293': 'ЭТП',
        '2295': 'Коннект',
        '2303': 'Кабинет садовода',
        '2311': 'БИТРИКС24',
        '2357': 'Линк',
        '2353': 'Не указан',
        '2343': 'ГРМ Спец',
        '2349': 'ДУО',
        '2355': '',
        '': ''
    }
    for element in companies_interaction_info:
        if month_int_names[datetime.now().month] in element['NAME']:
            companies_top_deal.setdefault(list(element['PROPERTY_1299'].values())[0], element_deal_type_name[list(element['PROPERTY_1377'].values())[0]])
    companies_interaction_count = list(map(lambda x: list(x['PROPERTY_1299'].values())[0], companies_interaction_info))
    companies_without_interaction = {}
    for deal in its_deals:
        months_without_interaction = len(list(filter(lambda x: x == deal['COMPANY_ID'], companies_interaction_count)))
        if months_without_interaction == 3:
            if deal['ASSIGNED_BY_ID'] not in companies_without_interaction:
                companies_without_interaction.setdefault(deal['ASSIGNED_BY_ID'], set())
            companies_without_interaction[deal['ASSIGNED_BY_ID']].add(deal['COMPANY_ID'])

    for responsible in companies_without_interaction:
        task = b.call('tasks.task.add', {
            'fields': {
                'TITLE': 'Компании без взаимодействия',
                'RESPONSIBLE_ID': '1' if req['responsibles'] == 'N' else responsible,
                'CREATED_BY': '173',
                'DESCRIPTION': 'По данным системы, с этими компаниями последнее взаимодействие произошло свыше 90 дней. Пожалуйста, свяжитесь с клиентами и/или укажите актуальные контактные данные в карточке компании и контактов',
                'DEADLINE': f"{datetime.strftime(task_deadline_date, '%Y-%m-%d')} 19:00",

            }
        }, raw=True)['result']

        for company in companies_without_interaction[responsible]:
            company_info = list(filter(lambda x: x['ID'] == company, companies))
            if company_info:
                company_id = company_info[0]['ID']
                company_name = company_info[0]['TITLE']
                top_deal = companies_top_deal[company_info[0]['ID']]
                b.call('task.checklistitem.add', {
                           'TASKID': task['task']['id'],
                           'FIELDS': {
                               'TITLE': f"{company_name} {top_deal} https://vc4dk.bitrix24.ru/crm/company/details/{company_id}/"}
                           } , raw=True)
                sleep(1)



if __name__ == '__main__':
    send_company_interaction_info()