import re
from datetime import datetime

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
    companies = b.get_all('crm.company.list', {
        'select': ['*', 'UF_*', 'PHONE'],
        'filter': {
            'ID': list(map(lambda x: x['COMPANY_ID'], deals))
        }
    })
    data_to_write = []
    for index, deal in enumerate(deals, 1):
        print(deal)
        deal_date_start = datetime.fromisoformat(deal['BEGINDATE']).strftime('%d.%m.%Y')
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
        })[0]
        company_city = company_requisite['ADDRESS_CITY'] if 'ADDRESS_CITY' in company_requisite and company_requisite['ADDRESS_CITY'] else 'Санкт-Петербург'
        company_info = list(filter(lambda x: x['ID'] == deal['COMPANY_ID'], companies))[0]
        company_name = re.match(r'.+ \d+', company_info['TITLE']).group()
        if 'PHONE' in company_info and company_info['PHONE']:
            company_phone_code = company_info['PHONE'][0]['VALUE'][1:4]
            company_phone = company_info['PHONE'][0]['VALUE'][4:]
        else:
            company_phone_code = '812'
            company_phone = '334-44-74'
        print(company_requisite)
        print(company_info)
        contacts = b.get_all('crm.company.contact.items.get', {
            'id': company_info['ID']
        })
        if contacts:
            contact_info = b.get_all('crm.contact.get', {
                'ID': contacts[0]['CONTACT_ID']
            })
            responsible_name = f"{contact_info['LAST_NAME']} " \
                               f"{contact_info['NAME']} " \
                               f"{contact_info['SECOND_NAME']}".replace('None', '').strip()
        else:
            responsible_name = 'Иванов Иван Иванович'
        data_to_write.append([
            index,                              # № п/п
            '04382',                            # Код партнера
            '1',                                # Способ получения
            'p1857',                            # Код дистрибутора
            code_1c,                            # Вид 1С:ИТС
            deal['UF_CRM_1640523562691'],       # РегНомер
            company_name,                       # Наименование фирмы
            company_requisite['RQ_INN'],        # ИНН
            company_requisite['RQ_KPP'],        # КПП
            1,                                  # Количество рабочих мест
            '',
            '',
            responsible_name,                   # Ответственный
            '',
            company_city,                       # Город !!! ИСПРАВИТЬ
            '',
            '',
            '',
            '',
            company_phone_code,                 # Код
            company_phone,                      # Телефон
            '',
            '',
            '0-новая',                          #
            '',
            '',
            deal_date_start,                    # Дата начала





        ])
        print(data_to_write)

create_its_applications_file()
