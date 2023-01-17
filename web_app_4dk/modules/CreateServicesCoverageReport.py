from datetime import datetime
import os
import base64

from fast_bitrix24 import Bitrix
import openpyxl

from web_app_4dk.modules.field_values import deals_category_1_types, departments_id_name, month_int_names
from web_app_4dk.modules.EdoInfoHandler import month_codes, year_codes
from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def create_services_coverage_report(req):
    result_data = {}
    companies_info = b.get_all('crm.company.list')
    users_info = b.get_all('user.get')
    deals_info = b.get_all('crm.deal.list', {
        'select': [
            'TYPE_ID',
            'COMPANY_ID',
            'ASSIGNED_BY_ID',
            'TITLE',
            'UF_CRM_1640523562691',      # Регномер
            'UF_CRM_1657878818384',      # Группа
            'UF_CRM_1640523703',         # Подразделение
            'UF_CRM_1651071211',         # Льготная отчетность
        ],
        'filter': {
            'STAGE_ID': ['C1:NEW', 'C1:UC_0KJKTY', 'C1:UC_3J0IH6', 'C1:UC_KZSOR2', 'C1:UC_VQ5HJD'],
            '!TYPE_ID': ['GOODS', 'UC_K9QJDV', 'UC_D7TC4I', 'UC_IUJR81'],
        }})
    extra_clouds_info = b.get_all('crm.deal.list', {
        'select': [
            'COMPANY_ID',
            'TITLE',
            'UF_CRM_1640523562691',     # Регномер
        ],
        'filter': {
            'TYPE_ID': 'UC_IUJR81',
            'STAGE_ID': ['C1:NEW', 'C1:UC_0KJKTY', 'C1:UC_3J0IH6', 'C1:UC_KZSOR2', 'C1:UC_VQ5HJD'],
        }
    })

    # Создание базового массива с ИТС
    deals_its = list(filter(lambda x: x['UF_CRM_1657878818384'] == '859', deals_info))
    for deal in deals_its:
            if deal['COMPANY_ID'] not in result_data:
                result_data.setdefault(deal['COMPANY_ID'], [])
            company_info = list(filter(lambda x: x['ID'] == deal['COMPANY_ID'], companies_info))[0]
            user_name = ''
            user_info = list(filter(lambda x: x['ID'] == deal['ASSIGNED_BY_ID'], users_info))
            if user_info:
                user_info = user_info[0]
                user_name = f"{user_info['NAME']} {user_info['LAST_NAME']}"
            company_name = ''
            if deal['COMPANY_ID']:
                company_info = list(filter(lambda x: x['ID'] == deal['COMPANY_ID'], companies_info))[0]
                company_name = company_info['TITLE']
            deal_reporting_in_its = 'Нет'
            if deal['UF_CRM_1651071211']:
                deal_reporting_in_its = 'Да'
            field_values = {
                'Компания': company_name,
                'ИТС': deals_category_1_types[deal['TYPE_ID']],
                'Регномер': deal['UF_CRM_1640523562691'],
                'Ответственный за сделку ИТС': user_name,
                'Подразделение ответственного': departments_id_name[deal['UF_CRM_1640523703']],
                'Контрагент': 'Нет',
                'Спарк в договоре / Спарк 3000': 'Нет',
                'Спарк Плюс': 'Нет',
                'РПД': '',
                'ЭДО': 0,
                'Отчетность': 0,
                'Отчетность в рамках ИТС': deal_reporting_in_its,
                'Допы Облако': '',
            }
            result_data[deal['COMPANY_ID']].append(field_values)

    # Подсчет сервисов из массива сделок
    services = [
        'UC_A7G0AM',        # Контрагент
        'UC_2B0CK2',        # 1Спарк в договоре
        'UC_86JXH1',        # 1Спарк 3000
        'UC_WUGAZ7',        # 1СпаркРиски ПЛЮС 22500
        'UC_GZFC63',        # РПД
        'UC_IUJR81',        # Допы Облако
    ]
    deals_services = list(filter(lambda x: x['TYPE_ID'] in services, deals_info))
    for service in deals_services:
        if service['COMPANY_ID']:
            if service['COMPANY_ID'] in result_data:
                for data_counter in range(len(result_data[service['COMPANY_ID']])):
                        if service['TYPE_ID'] == 'UC_A7G0AM':
                            result_data[service['COMPANY_ID']][data_counter]['Контрагент'] = 'Да'
                        elif service['TYPE_ID'] in ['UC_2B0CK2', 'UC_86JXH1']:
                            result_data[service['COMPANY_ID']][data_counter]['Спарк в договоре / Спарк 3000'] = 'Да'
                        elif service['TYPE_ID'] == 'UC_WUGAZ7':
                            result_data[service['COMPANY_ID']][data_counter]['Спарк Плюс'] = 'Да'
                        elif service['TYPE_ID'] == 'UC_GZFC63':
                            result_data[service['COMPANY_ID']][data_counter]['РПД'] += f"{service['TITLE']}, "

    # Подсчет Допов Облако
    for extra_cloud in extra_clouds_info:
        if extra_cloud['COMPANY_ID']:
            if extra_cloud['COMPANY_ID'] in result_data:
                data_counter = 0
                for company_result_data in result_data[extra_cloud['COMPANY_ID']]:
                        result_data[extra_cloud['COMPANY_ID']][data_counter]['Допы Облако'] += f"{extra_cloud['TITLE']}, "
                        data_counter += 1

    # Подсчет ЭДО
    year = datetime.now().year
    last_month_number = datetime.now().month - 1
    if last_month_number == 0:
        last_month_number = 12
        year -= 1
    edo_info_list = b.get_all('lists.element.get', {
        'IBLOCK_TYPE_ID': 'lists',
        'IBLOCK_ID': '235',
        'filter': {'PROPERTY_1567': month_codes[month_int_names[last_month_number]],
                   'PROPERTY_1569': year_codes[str(year)]
                   }})
    for edo_info in edo_info_list:
        if 'PROPERTY_1571' in edo_info:
            edo_info_company_id = list(edo_info['PROPERTY_1571'].values())[0]
            if edo_info_company_id in result_data:
                edo_info_value = int(list(edo_info['PROPERTY_1573'].values())[0])
                for data_counter in range(len(result_data[edo_info_company_id])):
                    result_data[edo_info_company_id][data_counter]['ЭДО'] = edo_info_value

    # Подсчет отчетностей
    for company_id in result_data:
        for data_counter in range(len(result_data[company_id])):
            deals_reporting = list(filter(lambda x: x['TYPE_ID'] == 'UC_O99QUW' and x['COMPANY_ID'] == company_id, deals_info))
            if deals_reporting:
                result_data[company_id][data_counter]['Отчетность'] = len(deals_reporting)

    # Запись отчета
    report_name = f"Отчет_по_охвату_сервисами_{datetime.now().strftime('%d-%m-%Y-%f')}.xlsx"
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    data_to_write = []
    titles = []
    for company_id in result_data:
        if not titles:
            titles = list(result_data[company_id][0].keys())
        for data in result_data[company_id]:
            data['РПД'] = data['РПД'].rstrip(', ')
            data['Допы Облако'] = data['Допы Облако'].rstrip(', ')
            data_to_write.append(list(data.values()))
    data_to_write = sorted(data_to_write, key=lambda x: (x[3].split()[1], x[0]))
    worksheet.append(titles)
    for row in data_to_write:
        worksheet.append(row)
    workbook.save(report_name)

    # Загрузка отчета в Битрикс
    bitrix_folder_id = '293499'
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
        'MESSAGE': f'Отчет по охвату сервисами сформирован. {upload_report["DETAIL_URL"]}'})
    os.remove(report_name)