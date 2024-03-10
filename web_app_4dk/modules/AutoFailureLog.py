from datetime import datetime, timedelta

from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication



b = Bitrix(authentication('Bitrix'))


def auto_failure_log(req):
    logs = 'Сделки для отказа:\n\n'
    filter_date = datetime.strptime(req['date'], '%d.%m.%Y')
    filter_date_month = filter_date.month
    filter_date_year = filter_date.year
    for i in range(2):
        filter_date_month += 1
        if filter_date_month == 13:
            filter_date_month = 1
            filter_date_year += 1
    filter_date_end = datetime(day=1, month=filter_date_month, year=filter_date_year) - timedelta(days=2)
    filter_date_end = datetime.strftime(filter_date_end, '%Y-%m-%d')
    filter_date_start = datetime.strftime(filter_date, '%Y-%m-%d')
    deal_types = [
        'UC_HT9G9H',  # ПРОФ Земля
        'UC_XIYCTV',  # ПРОФ Земля+Помощник
        'UC_5T4MAW',  # ПРОФ Земля+Облако+Помощник
        'UC_N113M9',  # ПРОФ Земля+Облако
        'UC_AVBW73',  # Базовый Земля
        'UC_92H9MN',  # Индивидуальный
        'UC_81T8ZR',  # АОВ
        'UC_SV60SP'
    ]
    deals = b.get_all('crm.deal.list', {
        'select': ['*', 'UF_*'],
        'filter': {'>=UF_CRM_1638958630625': filter_date_start,
                  '<=UF_CRM_1638958630625': filter_date_end,
                   'UF_CRM_1637933869479': '1',
                   'TYPE_ID': deal_types
                   }})
    if deals:
        companies = b.get_all('crm.company.list', {'filter': {'ID': list(map(lambda x: x['COMPANY_ID'], deals))}})

    log_list = []
    for index, deal in enumerate(deals, 1):

        company = list(filter(lambda x: x['ID'] == deal['COMPANY_ID'], companies))
        if company:
            list_element = [company[0]["TITLE"],deal["TITLE"],deal["ID"]]
        else:
            list_element = [' ',deal["TITLE"],deal["ID"]]
        log_list.append(list_element)
    log_list.sort(key=lambda x: x[0])
    for i in range (len(log_list)):
        logs += f'{i+1}. {log_list[i][0]} {log_list[i][1]} {log_list[i][2]}\n'


    b.call('im.notify.system.add', {
        'USER_ID': req['user_id'][5:],
        'MESSAGE': logs})
