from time import time

from fast_bitrix24 import Bitrix
import openpyxl


b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')

month_codes = {
    'Январь': '2371',
    'Февраль': '2373',
    'Март': '2375',
    'Апрель': '2377',
    'Май': '2379',
    'Июнь': '2381',
    'Июль': '2383',
    'Август': '2385',
    'Сентябрь': '2387',
    'Октябрь': '2389',
    'Ноябрь': '2391',
    'Декабрь': '2393'
}

year_codes = {
    '2022': '2395',
    '2023': '2397'
}


def read_xlsx(filename: str) -> list:
    workbook = openpyxl.load_workbook(filename)
    worksheet = workbook.active
    max_rows = worksheet.max_row
    max_columns = worksheet.max_column
    data = []
    titles = {}
    ignore_client_values = [None, '0', 'None']
    ignore_package_count = [None, '0', 'None']
    for row in range(1, max_rows + 1):
        temp = {}
        for column in range(1, max_columns + 1):
            cell_value = str(worksheet.cell(row, column).value)
            #if row == 5:
            if row == 1:
                titles.setdefault(column, cell_value)
            else:
                if not titles:
                    continue
                temp.setdefault(titles[column], cell_value)
        if temp:
            if temp['Сумма для клиента'] in ignore_client_values and temp['Сумма пакетов по владельцу'] in ignore_package_count:
                continue
            data.append(temp)

    return data


def get_service_list_elements() -> list:
    elements = b.get_all('lists.element.get', {'IBLOCK_TYPE_ID': 'lists', 'IBLOCK_ID': '169'})
    elements = list(map(lambda x: {'COMPANY_ID':  list(x['PROPERTY_1283'].values())[0], 'SUBSCRIBER_CODE': list(x['PROPERTY_1289'].values())[0]}, elements))
    return elements


def create_edo_list_element(month:str, year:str, data:dict):
    b.call('lists.element.add', {'IBLOCK_TYPE_ID': 'lists', 'IBLOCK_ID': '235', 'ELEMENT_CODE': time(), 'FIELDS': {
        'NAME': f"{month} {year}",
        'PROPERTY_1567': month_codes[month],
        'PROPERTY_1569': year_codes[year],
        'PROPERTY_1571': data['Компания'],
        'PROPERTY_1573': data['Сумма пакетов по владельцу'] if data['Сумма пакетов по владельцу'] != 'None' else '0',
        'PROPERTY_1575': data['Сумма для клиента'] if data['Сумма для клиента'] != 'None' else '0',
        'PROPERTY_1577': data['Регномер'] if 'Регномер' in data else '',
        'PROPERTY_1579': data['Владелец ИТС'] if 'Владелец ИТС' in data else '',
        'PROPERTY_1581': data['Ответственный за ИТС'] if 'Ответственный за ИТС' in data else ''
    }})


def edo_info_handler(month: str, year: str, filename: str):
    not_found = []
    file_data = read_xlsx(filename)
    service_list_elements = get_service_list_elements()
    companies = b.get_all('crm.company.list', {'select': ['*', 'UF_*']})
    deals = b.get_all('crm.deal.list', {'select': ['*', 'UF_*'], 'filter': {'CATEGORY_ID': '1'}})
    for data in file_data:

        # Поиск компании по ИНН
        company = list(filter(lambda x: x['UF_CRM_1656070716'] == data['ИНН клиента'], companies))
        company_link_company = None
        if company:
            company = company[0]
            data.setdefault('Компания', company['ID'])
            if company['UF_CRM_1662385947']:
                company_link_company = company['UF_CRM_1662385947'][0]
        else:

            # Поиск компании по коду подписчика в УС "Отчет по сервисам"
            subscriber_code = data['Владелец'].split()[0]
            elements = list(filter(lambda x: x['SUBSCRIBER_CODE'] == subscriber_code, service_list_elements))
            if elements:
                data.setdefault('Компания', elements[0]['COMPANY_ID'])
            else:
                data.setdefault('Ошибка', 'Не найдена компания')
                not_found.append(data)
                continue

        # Поиск ИТС по компании
        company_deal = list(filter(lambda x: x['COMPANY_ID'] == data['Компания'], deals))
        if company_deal:
            data.setdefault('Регномер', company_deal[0]['UF_CRM_1640523562691'])
            company_its = list(filter(lambda x: x['UF_CRM_1640523562691'] == data['Регномер'] and x['UF_CRM_1657878818384'] == '859', deals))
            if company_its:
                data.setdefault('Владелец ИТС', company_its[0]['COMPANY_ID'])
                data.setdefault('Ответственный за ИТС', company_its[0]['ASSIGNED_BY_ID'])

        # Поиск ИТС по значению поля компании "Связан с"
        if 'Владелец ИТС' not in data and company_link_company:
            company_its = list(filter(lambda x: x['COMPANY_ID'] == company_link_company and x['UF_CRM_1657878818384'] == '859', deals))
            if company_its:
                data.setdefault('Владелец ИТС', company_its[0]['COMPANY_ID'])
                data.setdefault('Ответственный за ИТС', company_its[0]['ASSIGNED_BY_ID'])
                data.setdefault('Регномер', company_its[0]['UF_CRM_1640523562691'])

        create_edo_list_element(month, year, data)

    not_found_titles = list(not_found[0].keys())
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.append(not_found_titles)
    for row in not_found:
        worksheet.append(list(row.values()))
    file_name = f"Ошибки за {month} {year}.xlsx"
    workbook.save(file_name)

edo_info_handler('Ноябрь', '2022', '11-2022.xlsx')