from fast_bitrix24 import Bitrix
import dateutil.parser
from datetime import datetime
import openpyxl


b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')

deal = b.get_all('crm.deal.list', {'select': ['UF_CRM_1657878818384'], 'filter': {'ID': '100795'}})

users_info = b.get_all('user.get')

accounting_deals = b.get_all('crm.deal.list', {
    'select': ['*', 'UF_*'],
    'filter': {
        'CATEGORY_ID': '1',
        'STAGE_ID': [
            'C1:NEW',
            'C1:UC_0KJKTY',
            'C1:UC_3J0IH6',
        ],
        'UF_CRM_1657878818384': '905',      # Группа == Отчетность
        '!UF_CRM_1637934357592': '165',     # Вендор ЭЦП != ФНС
        '>UF_CRM_1637934330556': '2022-11-30',      # Срок действия ЭЦП
        '<UF_CRM_1637934330556': '2023-04-1',      # Срок действия ЭЦП
    }
})

its_deals = b.get_all('crm.deal.list', {
    'select': ['*', 'UF_*'],
    'filter': {
        'CATEGORY_ID': '1',
        'STAGE_ID': [
                        'C1:NEW',  # Услуга активна
                        'C1:UC_0KJKTY',  # Счет сформирован
                        'C1:UC_3J0IH6',  # Счет отправлен клиенту
                        'C1:UC_KZSOR2',  # Нет оплаты
                        'C1:UC_VQ5HJD',  # Ждём решения клиента
                    ],
    }
})

companies = b.get_all('crm.company.list')

single_deals = []
gk_deals = []
used_regnumbers = []

gk_count = 0
used_responsibles = []

for accounting_deal in accounting_deals:
    regnumber = accounting_deal['UF_CRM_1640523562691']
    regnumber_filtered_deals = list(filter(lambda x: x['UF_CRM_1640523562691'] == regnumber, accounting_deals))
    if len(regnumber_filtered_deals) == 1:
        responsible = accounting_deal['ASSIGNED_BY_ID']
        if responsible in used_responsibles:
            continue
        its_filtered_deals = list(filter(lambda x: x['UF_CRM_1640523562691'] == regnumber, its_deals))
        if its_filtered_deals:
            responsible = its_filtered_deals[0]['ASSIGNED_BY_ID']
        task_date_end = accounting_deal['UF_CRM_1637934330556']
        uf_crm_deal = f"D_{accounting_deal['ID']}"
        uf_crm_company = f"CO_{accounting_deal['COMPANY_ID']}"
        company_name = list(filter(lambda x: x['ID'] == accounting_deal['COMPANY_ID'], companies))[0]['TITLE']
        task_name = f"Смена ЭЦП"
        responsible_info = list(filter(lambda x: x['ID'] == responsible, users_info))[0]
        responsible_name = f"{responsible_info['NAME']} {responsible_info['LAST_NAME']}"
        task_date_end_str = datetime.strftime(dateutil.parser.isoparse(task_date_end), "%d.%m.%Y")
        task_date_end_b24 = datetime.strftime(dateutil.parser.isoparse(task_date_end), "%Y-%m-%d") + ' 19:00:00'
        b.call('tasks.task.add', {
            'fields': {
                'RESPONSIBLE_ID': '91',
                'TITLE': f"Смена ЭЦП {responsible_name}",
                'GROUP_ID': '89',
                'DEADLINE': task_date_end_b24,
                'UF_CRM_TASK': [uf_crm_company, uf_crm_deal],
                'DESCRIPTION': "75% наших клиентов на 1С-отчетность используют ЭЦП, которые перестанут работать через месяц. Это более 2200 штук. Требуется узнать, по каждому ИНН, получил пользователь ЭЦП от ФНС, если не получил - еще раз направить в ФНС и зафиксировать дату следующего контакта, а если уже получил, то решить, когда клиент готов ее ввести в сервис. Завершением задачи будет либо обработанное заявление с подписью ФНС, или отказ клиента от использования сервиса.",
                'AUTHOR_ID': '173'
            }
        })
        used_responsibles.append(responsible)
    else:
        if regnumber in used_regnumbers or gk_count == 5:
            continue
        regnumber_filtered_deals_count = len(regnumber_filtered_deals)
        responsible = regnumber_filtered_deals[0]['ASSIGNED_BY_ID']
        its_accounting_deals = list(filter(lambda x: x['TYPE_ID'] == 'UC_OV4T7K' and x['UF_CRM_1640523562691'] == regnumber, accounting_deals))
        if its_accounting_deals:
            responsible = its_accounting_deals[0]['ASSIGNED_BY_ID']
        else:
            its_filtered_deals = list(filter(lambda x: x['UF_CRM_1640523562691'] == regnumber, its_deals))
            if its_accounting_deals:
                responsible = its_accounting_deals[0]['ASSIGNED_BY_ID']
        regnumber_filtered_deals_date_map = list(map(lambda x: [x['ID'], dateutil.parser.isoparse(x['UF_CRM_1637934330556']), x['TITLE']], regnumber_filtered_deals))
        regnumber_filtered_deals_date_filtered = list(sorted(regnumber_filtered_deals_date_map, key=lambda x: x[1]))
        early_deal_id = regnumber_filtered_deals_date_filtered[0][0]
        gk_filtered_deal = list(filter(lambda x: x['ID'] == early_deal_id, regnumber_filtered_deals))[0]
        task_date_end = gk_filtered_deal['UF_CRM_1637934330556']
        task_name = 'Смена ЭЦП ГК'
        for deal in regnumber_filtered_deals:
            if 'UF_CRM_1637934121' in deal and deal['UF_CRM_1637934121'] is not None:
                gk_or_company = deal['UF_CRM_1637934121']
                gk_or_company = list(filter(lambda x: x['ID'] == deal['COMPANY_ID'], companies))[0]['TITLE']
                task_name += f" {gk_or_company}"
                break
        if task_name == 'Смена ЭЦП ГК':
            company_id = list(filter(lambda x: x['ID'] == early_deal_id, regnumber_filtered_deals))[0]['COMPANY_ID']
            company_name = list(filter(lambda x: x['ID'] == company_id, companies))[0]['TITLE']
            gk_or_company = company_name
            task_name += f" {company_name}"
        used_regnumbers.append(regnumber)
        responsible_info = list(filter(lambda x: x['ID'] == responsible, users_info))[0]
        responsible_name = f"{responsible_info['NAME']} {responsible_info['LAST_NAME']}"
        task_date_end_str = datetime.strftime(dateutil.parser.isoparse(task_date_end), "%d.%m.%Y")
        task_date_end_b24 = datetime.strftime(dateutil.parser.isoparse(task_date_end), "%Y-%m-%d") + ' 19:00:00'
        gk_deals.append([accounting_deal['ID'], responsible_name, task_date_end_str, regnumber_filtered_deals_count])
        gk_task = b.call('tasks.task.add', {
            'fields': {
                'RESPONSIBLE_ID': '91',
                'TITLE': f"{task_name} {responsible_name}",
                'GROUP_ID': '89',
                'DEADLINE': task_date_end_b24,
                'DESCRIPTION': "75% наших клиентов на 1С-отчетность используют ЭЦП, которые перестанут работать через месяц. Это более 2200 штук. Требуется узнать, по каждому ИНН, получил пользователь ЭЦП от ФНС, если не получил - еще раз направить в ФНС и зафиксировать дату следующего контакта, а если уже получил, то решить, когда клиент готов ее ввести в сервис. Завершением задачи будет либо обработанное заявление с подписью ФНС, или отказ клиента от использования сервиса.",
                'STAGE_ID': '1277',
                'AUTHOR_ID': '173'
            }
        })['task']['id']
        for deal in regnumber_filtered_deals:
            company_name = list(filter(lambda x: x['ID'] == deal['COMPANY_ID'], companies))[0]['TITLE']
            deal_name = deal['TITLE']
            ecp_validity_period = deal['UF_CRM_1637934330556']
            deal_url = f"https://vc4dk.bitrix24.ru/crm/deal/details/{deal['ID']}/"
            b.call('task.checklistitem.add', [
                gk_task, {
                    'TITLE': f"{company_name} {deal_name} {datetime.strftime(dateutil.parser.isoparse(ecp_validity_period), '%d.%m.%Y')} {deal_url}",
                }
            ], raw=True
                   )
        gk_count += 1


''''
workbook = openpyxl.Workbook()
worksheet = workbook.active
worksheet.title = 'Уникальный регномер'
worksheet.append(['ID', 'Ответственный', 'Крайний срок', 'Компания', 'Сделка'])
for row in single_deals:
    worksheet.append(row)
worksheet = workbook.create_sheet('ГК')
worksheet.append(['ID', 'Ответственный', 'Крайний срок', 'Кол-во элементов'])
for row in gk_deals:
    worksheet.append(row)
workbook.save('test.xlsx') 
'''


