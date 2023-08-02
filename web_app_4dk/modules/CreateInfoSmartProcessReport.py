import os
from datetime import datetime
import base64

from fast_bitrix24 import Bitrix
import openpyxl

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))
base_types = {
    '1569': 'ЗУП',

}


def create_info_smart_process_report(req):
    companies = b.get_all('crm.company.list', {
        'filter': {
            '!COMPANY_TYPE': ['UC_RTNQP4', 'UC_E99TUC', 'UC_8TI0LB']
        }
    })
    info_elements = b.get_all('crm.item.list', {
        'entityTypeId': '141'
    })
    fields = b.get_all('crm.item.fields', {
        'entityTypeId': '141',
    })
    users = b.get_all('user.get')
    result = [
        ['Компания', 'Ответственный', 'Есть инфо', 'Комментарий', 'Наличие доработок (нетиповая конфигурация)', 'Путь к базе', 'Конфигурация', 'Название базы']
    ]
    for company in companies:
        company_data = list()
        company_data.append(list(filter(lambda x: str(x['ID']) == str(company['ID']), companies))[0]['TITLE'])

        user = list(filter(lambda x: str(company['ASSIGNED_BY_ID']) == str(x['ID']), users))
        if user:
            company_data.append(f'{user[0]["LAST_NAME"]} {user[0]["NAME"]}')

        info = list(filter(lambda x: str(company['ID']) == str(x['companyId']), info_elements))
        if info:
            company_data.append('Да')
            company_data.append(' '.join(list(map(lambda x: x.replace('\n', ' '), info[0]['ufCrm25_1666342439']))))
            company_data.append(info[0]['ufCrm25_1689337909'])
            company_data.append(info[0]['ufCrm25_1689337900'])
            company_data.append(list(filter(lambda x: str(x['ID']) == str(info[0]['ufCrm25_1689337857']), fields['fields']['ufCrm25_1689337857']['items']))[0]['VALUE'] if info[0]['ufCrm25_1689337857'] else '')
            company_data.append(info[0]['ufCrm25_1689337847'])
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