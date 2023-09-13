from datetime import datetime, timedelta

from fast_bitrix24 import Bitrix
import requests

from web_app_4dk.modules.authentication import authentication
from web_app_4dk.modules.web_app_ip import web_app_ip


b = Bitrix(authentication('Bitrix'))


def auto_failure(req):
    logs = 'Обработанные сделки:\n\n'
    filter_date = datetime.strptime(req['date'], '%d.%m.%Y')
    filter_date_end = datetime(day=1, month=filter_date.month + 2, year=filter_date.year) - timedelta(days=2)
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

    for index, deal in enumerate(deals, 1):
        b.call('bizproc.workflow.start', {'TEMPLATE_ID': '759', 'DOCUMENT_ID': ['crm', 'CCrmDocumentDeal', 'DEAL_' + deal['ID']]})
        company = list(filter(lambda x: x['ID'] == deal['COMPANY_ID'], companies))
        if company:
            logs += f'{index}. {deal["ID"]} {deal["TITLE"]} {company[0]["TITLE"]}\n'
        else:
            logs += f'{index}. {deal["ID"]} {deal["TITLE"]}\n'

    b.call('im.notify.system.add', {
        'USER_ID': req['user_id'][5:],
        'MESSAGE': logs})

    requests.get(f'{web_app_ip}/bitrix/custom_webhook?job=create_its_applications_file&user_id={req["user_id"]}&process=reject')
