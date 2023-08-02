import os
from datetime import datetime
import base64

from fast_bitrix24 import Bitrix
import openpyxl

from web_app_4dk.modules.authentication import authentication
from web_app_4dk.modules.field_values import deals_category_1_types


b = Bitrix(authentication('Bitrix'))

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

def create_info_smart_process_report(req):
    companies = b.get_all('crm.company.list', {
        'filter': {
            '!COMPANY_TYPE': ['UC_RTNQP4', 'UC_E99TUC', 'UC_8TI0LB']
        }
    })
    deals = b.get_all('crm.deal.list', {
        'filter': {
            'CATEGORY_ID': '1'
        }
    })
    info_elements = b.get_all('crm.item.list', {
        'entityTypeId': '141'
    })
    fields = b.get_all('crm.item.fields', {
        'entityTypeId': '141',
    })
    users = b.get_all('user.get')
    departments = b.get_all('department.get')
    result = [
        ['Компания', 'Ответственный', 'Подразделение', 'Топ ИТС', 'Есть инфо', 'Комментарий', 'Наличие доработок (нетиповая конфигурация)', 'Путь к базе', 'Конфигурация', 'Название базы']
    ]
    for index, company in enumerate(companies, 1):
        print(index, len(companies))
        company_data = list()
        company_data.append(list(filter(lambda x: str(x['ID']) == str(company['ID']), companies))[0]['TITLE'])

        user = list(filter(lambda x: str(company['ASSIGNED_BY_ID']) == str(x['ID']), users))
        if user:
            company_data.append(f'{user[0]["LAST_NAME"]} {user[0]["NAME"]}')
            department = list(filter(lambda x: str(x['ID']) == str(user[0]['UF_DEPARTMENT'][0]), departments))[0]['NAME']
            if department:
                company_data.append(department)
            else:
                company_data.append('')

        deal = list(filter(lambda x: x['COMPANY_ID'] == company['ID'], deals))

        if deal:
            top_its = sort_types(list(map(lambda x: x['TYPE_ID'], deal)))
            if top_its:
                top_its = deals_category_1_types[top_its]
                company_data.append(top_its)
            else:
                company_data.append('')
        else:
            company_data.append('')

        info = list(filter(lambda x: str(company['ID']) == str(x['companyId']), info_elements))
        for i in info:
            company_data.append('Да')
            company_data.append(' '.join(list(map(lambda x: x.replace('\n', ' '), i['ufCrm25_1666342439']))))
            company_data.append(list(filter(lambda x: str(x['ID']) == str(i['ufCrm25_1689337909']), fields['fields']['ufCrm25_1689337909']['items']))[0]['VALUE'] if i['ufCrm25_1689337909'] else '')
            company_data.append(i['ufCrm25_1689337900'])
            company_data.append(list(filter(lambda x: str(x['ID']) == str(i['ufCrm25_1689337857']), fields['fields']['ufCrm25_1689337857']['items']))[0]['VALUE'] if i['ufCrm25_1689337857'] else '')
            company_data.append(i['ufCrm25_1689337847'])
            company_data = list(map(lambda x: '' if not x else x, company_data))
        else:
            company_data.append('Нет')
        result.append(company_data)

    report_name = f'Отчет_по_инфо_{datetime.now().strftime("%d_%m_%Y_%H_%M_%S")}.xlsx'
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    for row in result:
        worksheet.append(row)
    workbook.save(report_name)

    # Загрузка отчета в Битрикс
    bitrix_folder_id = '543059'
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
        'MESSAGE': f'Отчет по инфо сформирован. {upload_report["DETAIL_URL"]}'})
    os.remove(report_name)

create_info_smart_process_report({})