from fast_bitrix24 import Bitrix

import openpyxl

from web_app_4dk.modules.authentication import authentication
from web_app_4dk.tools import send_bitrix_request


b = Bitrix(authentication('Bitrix'))


def create_its_applications_file():
    workbook = openpyxl.load_workbook('Шаблон заявок ИТС.xlsx')
    worklist = workbook.active
    deals = b.get_all('crm.deal.list', {
        'select': ['*', 'UF_*'],
        'filter': {
            'UF_CRM_1643800749': '371',
            'CATEGORY_ID': '1'
        }
    })
    data_to_write = []
    for index, deal in enumerate(deals, 1):
        print(deal)
        product_row = send_bitrix_request('crm.deal.productrows.get', {
            'id': deal['ID'],
        })
        if not product_row:
            continue
        product_info = send_bitrix_request('crm.product.get.json', {
            'id': product_row[0]['PRODUCT_ID']
        })
        try:
            code_1c = product_info['PROPERTY_139']['value']
        except:
            continue
        company_requisite = send_bitrix_request('crm.requisite.list', {
            'filter': {
                'ENTITY_TYPE_ID': '4',
                'ENTITY_ID': deal['COMPANY_ID']
            }
        })
        print(company_requisite)
        data_to_write.append([
            index,                              # № п/п
            '04382',                            # Код партнера
            '1',                                # Способ получения
            'p1857',                            # Код дистрибутора
            code_1c,                            # Вид 1С:ИТС
            deal['UF_CRM_1640523562691'],       # РегНомер
            company_requisite[0][],        # Наименование фирмы
        ])
        print(data_to_write)
