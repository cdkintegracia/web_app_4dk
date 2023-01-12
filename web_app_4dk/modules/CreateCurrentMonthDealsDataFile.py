import os
import dateutil.parser
from datetime import datetime

from fast_bitrix24 import Bitrix
import openpyxl

from web_app_4dk.modules.field_values import deals_category_1_types, deals_category_1_stage_ids, UF_CRM_1657878818384_values


b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/78nouvwz9drsony0/')
deals_info_files_directory = f'/root/web_app_4dk/web_app_4dk/modules/deals_info_files/'


def create_current_month_deals_data_file(user_data=None, user_id='311'):
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
            'TYPE_ID',
            'ASSIGNED_BY_ID',
            'BEGINDATE',
            'CLOSEDATE',
            'OPPORTUNITY',
            'STAGE_ID',
            'UF_CRM_1657878818384',     # Группа
        ],
        'filter': {'CATEGORY_ID': '1'}})
    formatted_deals_info = []
    for deal in deals_info:
        temp = {}
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
            temp['Предполагаемая дата закрытия'] = datetime.strftime(closedate, '%d.%m.%Y')
        else:
            temp['Предполагаемая дата закрытия'] = ''
        if deal['BEGINDATE']:
            begindate = dateutil.parser.isoparse(deal['BEGINDATE'])
            temp['Дата начала'] = datetime.strftime(begindate, '%d.%m.%Y')
        else:
            temp['Дата начала'] = ''

        temp['Ответственный'] = user_name
        temp['Тип'] = deals_category_1_types[deal['TYPE_ID']]
        temp['Сумма'] = int(float(deal['OPPORTUNITY']))
        temp['Стадия сделки'] = deals_category_1_stage_ids[deal['STAGE_ID']]
        temp['Группа'] = UF_CRM_1657878818384_values[deal['UF_CRM_1657878818384']]
        temp['ID'] = deal['ID']
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