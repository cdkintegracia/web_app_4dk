import os
import dateutil.parser
from datetime import datetime
import asyncio

from fast_bitrix24 import Bitrix
import openpyxl

from web_app_4dk.modules.field_values import deals_category_1_types, deals_category_1_stage_ids, UF_CRM_1657878818384_values
from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))
#deals_info_files_directory = f'/root/web_app_4dk/web_app_4dk/modules/deals_info_files/'
deals_info_files_directory = f'/root/web_app_4dk/web_app_4dk/modules/deals_info_files/'


def get_companies(companies_id: list):
    return asyncio.run(b.get_all('crm.company.list', {
        'filter': {
            'ID': list(companies_id)
        }
    }))

def create_current_month_deals_data_file(user_data=None, user_id='1'):
    if not user_data:
        user_data = b.get_all('user.get')
    month_int_names = {
        1: 'Январь',
        2: 'Февраль',
        3: 'Март',
        4: 'Апрель',
        5: 'Май',
        6: 'Июнь',
        7: 'Июль',
        8: 'Август',
        9: 'Сентябрь',
        10: 'Октябрь',
        11: 'Ноябрь',
        12: 'Декабрь',
    }
    current_month = datetime.now().month
    current_year = datetime.now().year
    deals_info = b.get_all('crm.deal.list', {
        'select': [
            'TITLE',
            'TYPE_ID',
            'ASSIGNED_BY_ID',
            'BEGINDATE',
            'CLOSEDATE',
            'OPPORTUNITY',
            'STAGE_ID',
            'UF_CRM_1657878818384',     # Группа
            'COMPANY_ID',
            'UF_CRM_1640523562691',     # Регномер
            'UF_CRM_1638958630625',     # Дата проверки оплаты
        ],
        'filter': {'CATEGORY_ID': '1'}})
    companies_id = list(set(map(lambda x: x['COMPANY_ID'], list(filter(lambda x: 'COMPANY_ID' in x and x['COMPANY_ID'], deals_info)))))
    '''
    companies_info = b.get_all('crm.company.list', {
        'filter': {
            'ID': list(companies_id)
        }
    })
    '''
    companies_info = get_companies(companies_id)

    string_date_format = '%d.%m.%Y'
    formatted_deals_info = []
    for deal in deals_info:
        temp = {}

        company_user = ''
        if 'COMPANY_ID' in deal and deal['COMPANY_ID']:
            company_info = list(filter(lambda x: x['ID'] == deal['COMPANY_ID'], companies_info))[0]
            company_user = company_info['ASSIGNED_BY_ID']
        if company_user:
            company_user = list(filter(lambda x: x['ID'] == company_user, user_data))
            if company_user:
                company_user = company_user[0]
                company_user = f"{company_user['NAME']} {company_user['LAST_NAME']}"

        user_info = list(filter(lambda x: x['ID'] == deal['ASSIGNED_BY_ID'], user_data))
        if user_info:
            user_info = user_info[0]
        else:
            b.call('im.notify.system.add', {
                'USER_ID': user_id[5:],
                'MESSAGE': f'Для сделки с ID {deal["ID"]} не найден ответственный'})
        user_name = f"{user_info['NAME']} {user_info['LAST_NAME']}"

        if deal['CLOSEDATE']:
            closedate = dateutil.parser.isoparse(deal['CLOSEDATE'])
            temp['Предполагаемая дата закрытия'] = datetime.strftime(closedate, string_date_format)
        else:
            temp['Предполагаемая дата закрытия'] = ''
        if deal['BEGINDATE']:
            begindate = dateutil.parser.isoparse(deal['BEGINDATE'])
            temp['Дата начала'] = datetime.strftime(begindate, string_date_format)
        else:
            temp['Дата начала'] = ''
        temp['Ответственный'] = user_name
        temp['Тип'] = deals_category_1_types[deal['TYPE_ID']]
        temp['Сумма'] = int(float(deal['OPPORTUNITY']))
        temp['Стадия сделки'] = deals_category_1_stage_ids[deal['STAGE_ID']]
        temp['Группа'] = UF_CRM_1657878818384_values[deal['UF_CRM_1657878818384']]
        temp['ID'] = deal['ID']
        temp['Название сделки'] = deal['TITLE']
        temp['Компания'] = deal['COMPANY_ID'] if 'COMPANY_ID' in deal else ''
        temp['Ответственный за компанию'] = company_user
        temp['Регномер'] = deal['UF_CRM_1640523562691']
        #temp['Дата проверки оплаты'] = (datetime.fromisoformat(deal['UF_CRM_1638958630625'])).strftime(string_date_format) if deal['UF_CRM_1638958630625'] else ''
        temp['Дата проверки оплаты'] = (datetime.fromisoformat(deal['UF_CRM_1638958630625'])).strftime(string_date_format) + ' 03:00:00' if deal['UF_CRM_1638958630625'] else ''
        formatted_deals_info.append(temp)

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    titles = list(formatted_deals_info[0].keys())
    worksheet.append(titles)
    for deal in formatted_deals_info:
        worksheet.append(list(deal.values()))
    filename = f'{month_int_names[current_month]}_{current_year}.xlsx'
    workbook.save(f'{deals_info_files_directory}{filename}')


if __name__ == '__main__':
    create_current_month_deals_data_file()
