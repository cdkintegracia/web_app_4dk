from datetime import datetime
import re
if __package__:
    from .worklog_common import API, config, effective_seconds, hms
else:
    from worklog_common import API, config, effective_seconds, hms

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
        'UC_2R01AE', # Пакет услуг Базовый
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


TOTAL_HEADING = '[b]Использование лимита консультаций[/b]'
NO_ELEMENTS_TEXT = ('За выбранный диапазон договора не найдены месячные элементы. '
                    'Проверьте даты сделки и детализацию расхода.')


def update_total_description(description, text):
    """Заменяет только наш итог, сохраняя остальное описание и заметки менеджера."""
    description = description or ''
    # Старые произвольные BBCode-метки Битрикс мог перевести в нижний регистр
    # и дополнить закрывающими тегами. Удаляем и блок, и оставшиеся метки.
    description = re.sub(r'\[worklog_total_begin\].*?\[worklog_total_end\]',
                         '', description, flags=re.I | re.S)
    description = re.sub(r'\[/?worklog_total_(?:begin|end)\]',
                         '', description, flags=re.I)
    # В новом оформлении нет скрытых/неизвестных тегов. Узнаём наш блок по
    # заголовку и точному формату строки, а не удаляем всё после заголовка.
    total_line = (r'Расход консультаций с начала договора '
                  r'\(01\.\d{2}\.\d{4}\) = \d+:[0-5]\d:[0-5]\d\. '
                  r'Включены звонки и учтённые трудозатраты по задачам\.')
    block = (r'^' + re.escape(TOTAL_HEADING) + r'\r?\n(?:' + total_line +
             '|' + re.escape(NO_ELEMENTS_TEXT) + r')(?=\r?$)')
    description = re.sub(block, '', description, flags=re.I | re.M).rstrip()
    section = TOTAL_HEADING + '\n' + text
    return description + '\n\n' + section if description else section


def add_calls_amount_to_task(req):
    api=API(config())
    task_id=int(req['task_id']);company_id=int(req['company_id'])
    deals=api.pages('crm.deal.list', {
        'select':['COMPANY_ID','CLOSEDATE','TYPE_ID','UF_CRM_1638100416'],
        'filter':{'UF_CRM_1657878818384':'859','COMPANY_ID':company_id,
                  'CATEGORY_ID':'1','!STAGE_ID':['C1:WON','C1:LOSE']}})
    deal=find_top_deal_type(deals)
    if not deal:return
    # Сохраняем исходный диапазон договора: отдельное изменение его границ
    # не смешиваем с подключением трудозатрат.
    end=datetime.fromisoformat(deal['CLOSEDATE'])
    month,year=end.month,end.year
    names=[]
    if __package__:
        from .worklog_common import MONTHS
    else:
        from worklog_common import MONTHS
    for _ in range(int(deal['UF_CRM_1638100416'])-1):
        month-=1
        if not month:month=12;year-=1
        names.append(f'{MONTHS[month-1]} {year}')
    elements=api.pages('lists.element.get',dict(api.list_params(),FILTER={
        'PROPERTY_1299':company_id,'NAME':names})) if names else []
    if elements:
        total=sum(effective_seconds(r,api.c) for r in elements)
        text=f'Расход консультаций с начала договора (01.{month:02d}.{year}) = {hms(total)}. Включены звонки и учтённые трудозатраты по задачам.'
    else:
        text=NO_ELEMENTS_TEXT
    task=api.call('tasks.task.get',{'taskId':task_id,'select':['ID','DESCRIPTION']})['result']['task']
    description=update_total_description(task.get('description'),text)
    if description!=task.get('description'):
        api.call('tasks.task.update',{'taskId':task_id,'fields':{'DESCRIPTION':description}},write=True)
