from datetime import datetime
from datetime import timedelta
import time
import base64
import os

from fast_bitrix24 import Bitrix
import openpyxl

from web_app_4dk.modules.authentication import authentication


# Считывание файла authentication.txt

webhook = authentication('Bitrix')
b = Bitrix(webhook)


deal_type_names = {
        'UC_HT9G9H': 'ПРОФ Земля',
        'UC_XIYCTV': 'ПРОФ Земля+Помощник',
        'UC_N113M9': 'ПРОФ Земля+Облако',
        'UC_5T4MAW': 'ПРОФ Земля+Облако+Помощник',
        'UC_ZKPT1B': 'ПРОФ Облако',
        'UC_2SJOEJ': 'ПРОФ Облако+Помощник',
        'UC_81T8ZR': 'АОВ',
        'UC_SV60SP': 'АОВ+Облако',
        'UC_92H9MN': 'Индивидуальный',
        'UC_7V8HWF': 'Индивидуальный+Облако',
        'UC_AVBW73': 'Базовый Земля',
        'UC_GPT391': 'Базовый Облако',
        'UC_1UPOTU': 'ИТС Бесплатный',
        'UC_K9QJDV': 'ГРМ Бизнес',
        'GOODS': 'ГРМ',
        'UC_J426ZW': 'Садовод',
        'UC_DBLSP5': 'Садовод+Помощник',
        'UC_USDKKM': 'Медицина',
}


def sort_types(types):
    level_1 = [
        'UC_HT9G9H',    # ПРОФ Земля
        'UC_XIYCTV',    # ПРОФ Земля+Помощник
        'UC_N113M9',    # ПРОФ Земля+Облако
        'UC_5T4MAW',    # ПРОФ Земля+Облако+Помощник
        'UC_ZKPT1B',    # ПРОФ Облако
        'UC_2SJOEJ',    # ПРОФ Облако+Помощник
        'UC_81T8ZR',    # АОВ
        'UC_SV60SP',    # АОВ+Облако
        'UC_92H9MN',    # Индивидуальный
        'UC_7V8HWF',    # Индивидуальный+Облако
    ]
    level_2 = [
        'UC_AVBW73',    # Базовый Земля
        'UC_GPT391',    # Базовый Облако
        'UC_1UPOTU',    # ИТС Бесплатный
        'UC_K9QJDV',    # ГРМ Бизнес
        'GOODS',        # ГРМ
        'UC_J426ZW',    # Садовод
        'UC_DBLSP5',    # Садовод+Помощник
    ]
    level_3 = [
        'UC_USDKKM',    # Медицина
    ]
    for type in level_1:
        if type in types:
            return type
    for type in level_2:
        if type in types:
            return type
    for type in level_3:
        if type in types:
            return type


def get_calls_info(company_id: str, list_elements: list) -> dict:
    for list_element in list_elements:
        list_element_company_id = None
        for key in list_element['PROPERTY_1299']:
            list_element_company_id = list_element['PROPERTY_1299'][key]
        if list_element_company_id == company_id:
            call_duration = '00:00:00'
            call_count = '0'
            for key in list_element['PROPERTY_1303']:
                call_duration = list_element['PROPERTY_1303'][key]
            for key in list_element['PROPERTY_1305']:
                call_count = list_element['PROPERTY_1305'][key]
            return {'call_duration': call_duration, 'call_count': call_count}
    return {'call_duration': '00:00:00', 'call_count': '0'}



def create_line_consultation_report(req):
    month_codes = {
        'Январь': '01',
        'Февраль': '02',
        'Март': '03',
        'Апрель': '04',
        'Май': '05',
        'Июнь': '06',
        'Июль': '07',
        'Август': '08',
        'Сентябрь': '09',
        'Октябрь': '10',
        'Ноябрь': '11',
        'Декабрь': '12'
    }
    filter_date = f"{req['month']} {req['year']}"
    filter_date_start = f"{req['year']}-{month_codes[req['month']]}-01"
    filter_date_end = datetime.strptime(filter_date_start, '%Y-%m-%d') + timedelta(days=31)
    filter_date_end = f"{datetime.strftime(filter_date_end, '%Y-%m')}-01"
    list_elements = b.get_all('lists.element.get',
                              {'IBLOCK_TYPE_ID': 'lists', 'IBLOCK_ID': '175', 'filter': {'NAME': filter_date}})
    deals = b.get_all('crm.deal.list', {
        'filter': {
            'UF_CRM_1657878818384': '859',   # ИТС
            }})
    companies = b.get_all('crm.company.list')
    data_to_write = [
        [
            f"Отчет по ЛК за {req['month']} {req['year']}"
        ],
        [
        'Компания',
        'Топ ИТС',
        'Продолжительность звонков',
        'Количество звонков',
        'Количество обращений в Коннекте',
        'Длительность обращений в Коннекте'
    ]
    ]
    ignore_list = []
    count = 0
    for deal in deals:
        try:
            count += 1
            company_id = deal['COMPANY_ID']
            if company_id in ignore_list:
                continue
            tasks_duration_seconds = 0
            tasks = b.get_all('tasks.task.list', {
                'filter': {
                    '!UF_AUTO_499889542776': None,
                    '>=CREATED_DATE': filter_date_start,
                    '<CREATED_DATE': filter_date_end,
                    'UF_CRM_TASK': f"CO_{company_id}"
                }})
            for task in tasks:
                tasks_duration_seconds += int(task['durationFact'])
            tasks_duration_time = time.gmtime(tasks_duration_seconds)
            tasks_duration_time = time.strftime("%H:%M:%S", tasks_duration_time)
            company_info = list(filter(lambda x: x['ID'] == company_id ,companies))[0]
            company_name = company_info['TITLE']
            company_deals = list(filter(lambda x: x['COMPANY_ID'] == company_id, deals))
            company_deal_types = []
            for company_deal in company_deals:
                company_deal_id = company_deal['ID']
                company_deal_info = list(filter(lambda x: x['ID'] == company_deal_id ,deals))[0]
                company_deal_type = company_deal_info['TYPE_ID']
                company_deal_types.append(company_deal_type)
            company_deal_top_type = sort_types(company_deal_types)
            ignore_list.append(company_id)
            call_info = get_calls_info(company_id, list_elements)
            data_to_write.append(
                [
                    company_name,
                    deal_type_names[company_deal_top_type],
                    call_info['call_duration'],
                    call_info['call_count'],
                    len(tasks),
                    tasks_duration_time
                ]
            )
            print(f"{count} | {len(deals)}")
        except:
            pass
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        for data in data_to_write:
            worksheet.append(data)
        create_time = datetime.now().strftime('%d-%m-%Y-%f')
        report_name = f'Отчет_по_ЛК_{create_time}.xlsx'
        workbook.save(report_name)

    # Загрузка отчета в Битрикс
    bitrix_folder_id = '187139'
    with open(report_name, 'rb') as file:
        report_file = file.read()
    report_file_base64 = str(base64.b64encode(report_file))[2:]
    upload_report = b.call('disk.folder.uploadfile', {
        'id': bitrix_folder_id,
        'data': {'NAME': report_name},
        'fileContent': report_file_base64
    })
    b.call('im.notify.system.add', {
        'USER_ID': req['user_id'][5:],
        'MESSAGE': f'Отчет по ЛК за {req["month"]} {req["year"]} сформирован. {upload_report["DETAIL_URL"]}'})
    os.remove(report_name)
