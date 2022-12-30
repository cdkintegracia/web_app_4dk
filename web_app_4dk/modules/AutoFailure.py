from datetime import datetime

from fast_bitrix24 import Bitrix


b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')


def auto_failure(req):
    logs = 'Обработанные сделки:\n\n'
    filter_date = datetime.strptime(req['date'], '%d.%m.%Y')
    filter_date = datetime.strftime(filter_date, '%Y-%m-%d')
    deals = b.get_all('crm.deal.list', {'select': ['*', 'UF_*'], 'filter': {'UF_CRM_1638958630625': filter_date}})
    deal_types = [
        'UC_HT9G9H',  # ПРОФ Земля
        'UC_XIYCTV',  # ПРОФ Земля+Помощник
        'UC_5T4MAW',  # ПРОФ Земля+Облако+Помощник
        'UC_N113M9',  # ПРОФ Земля+Облако
        'UC_AVBW73',  # Базовый Земля
        'UC_92H9MN',  # Индивидуальный
        'UC_81T8ZR',  # АОВ
    ]
    for deal in deals:
        if deal['TYPE_ID'] not in deal_types:
            continue
        #b.call('bizproc.workflow.start', {'TEMPLATE_ID': '759', 'DOCUMENT_ID': ['crm', 'CCrmDocumentDeal', 'DEAL_' + deal['ID']]})
        logs += f'{deal["ID"]} {deal["TITLE"]}\n'

    b.call('im.notify.system.add', {
        'USER_ID': req['user_id'][5:],
        'MESSAGE': logs})

