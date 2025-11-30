from datetime import datetime

from fast_bitrix24 import Bitrix

try:
    from authentication import authentication
    from field_values import month_int_names
except ModuleNotFoundError:
    from web_app_4dk.modules.authentication import authentication
    from web_app_4dk.modules.field_values import month_int_names


b = Bitrix(authentication('Bitrix'))


def find_top_deal_type(deals):
    sort_1 = [
        'UC_XIYCTV',  # ПРОФ Земля+Помощник
        'UC_5T4MAW',  # ПРОФ Земля+Облако+Помощник
        'UC_2SJOEJ',  # ПРОФ Облако+Помощник
        'UC_81T8ZR',  # АОВ
        'UC_SV60SP',  # АОВ+Облако
    ]
    sort_2 = [
        'UC_N113M9',  # ПРОФ Земля+Облако
        'UC_ZKPT1B',  # ПРОФ Облако
        'UC_92H9MN',  # Индивидуальный,
        'UC_7V8HWF',  # Индивидуальный+Облако
        'UC_HT9G9H',  # ПРОФ Земля
    ]
    sort_3 = [
        'UC_1UPOTU',  # ИТС Бесплатный
    ]

    for sort in sort_1:
        for deal in deals:
            if deal['TYPE_ID'] == sort:
                return deal
    for sort in sort_2:
        for deal in deals:
            if deal['TYPE_ID'] == sort:
                return deal
    for sort in sort_3:
        for deal in deals:
            if deal['TYPE_ID'] == sort:
                return deal


def add_calls_amount_to_task(req):
    task_id = req['task_id']
    company_id = req['company_id']
    deals = b.get_all('crm.deal.list', {
        'select': ['COMPANY_ID', 'CLOSEDATE', 'TYPE_ID', 'UF_CRM_1638100416'],
        #2025-11-30 ИБС
        'filter': {'UF_CRM_1657878818384': '859', 'COMPANY_ID': company_id, 'CATEGORY_ID': '1','!STAGE_ID': ['C1:WON', 'C1:LOSE']}})
        #'filter': {'UF_CRM_1657878818384': '859', 'COMPANY_ID': company_id, '!STAGE_ID': ['C1:WON', 'C1:LOSE']}})
    deal_info = find_top_deal_type(deals)

    if not deal_info:
        return
    closedate = datetime.fromisoformat(deal_info['CLOSEDATE'])
    filter_month = closedate.month
    filter_year = closedate.year
    month_range = int(deal_info['UF_CRM_1638100416'])
    filter_names = []
    for i in range(0, month_range - 1):
        filter_month -= 1
        if filter_month == 0:
            filter_month = 12
            filter_year -= 1
        filter_names.append(f'{month_int_names[filter_month]} {filter_year}')
    elements = b.get_all('lists.element.get', {
        'IBLOCK_TYPE_ID': 'lists',
        'IBLOCK_ID': '175',
        'filter': {
            'NAME': filter_names,
            'PROPERTY_1299': company_id
        }
    })
    task = b.get_all('tasks.task.get', {'taskId': task_id})['task']
    if elements:
        calls_sum = None
        for element in elements:
            call_value = list(element['PROPERTY_1303'].values())[0]
            call_value = datetime.strptime(call_value, '%H:%M:%S')
            call_value = (call_value.hour * 3600) + (call_value.minute * 60) + (call_value.second)
            if not calls_sum:
                calls_sum = call_value
            else:
                calls_sum += call_value
        hours = calls_sum // 3600
        minutes = (calls_sum % 3600) // 60
        seconds = (calls_sum % 3600) % 60
        calls_sum = f"{hours}:{minutes}:{seconds}"
        if len(str(filter_month)) == 1:
            filter_month = '0' + str(filter_month)
        b.call('tasks.task.update', {'taskId': task_id, 'fields': {'DESCRIPTION': f"{task['description']}\n\nРасход с начала договора (01.{filter_month}.{filter_year}) = {calls_sum}"}})
    else:
        b.call('tasks.task.update', {'taskId': task_id, 'fields': {'DESCRIPTION': f"{task['description']}\n\nВ Б24 сделка начинается позже текущей даты, поэтому посчитайте суммарное время самостоятельно"}})



