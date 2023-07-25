from fast_bitrix24 import Bitrix
import openpyxl

from authentication import authentication


b = Bitrix(authentication('Bitrix'))


revenue_elements = b.get_all('lists.element.get', {
    'IBLOCK_TYPE_ID': 'lists',
    'IBLOCK_ID': '257',
    'filter': {
        '>PROPERTY_1635': 199,
        'PROPERTY_1643': 2022
    }
})

companies = list(map(lambda x: list(x['PROPERTY_1631'].values())[0], revenue_elements))
companies_info = b.get_all('crm.company.list', {
    'filter': {
        'ID': companies,
        'COMPANY_TYPE': ['CUSTOMER', 'OTHER']
    }
})
deals = b.get_all('crm.deal.list', {
    'filter': {
        'COMPANY_ID': companies,
        'TYPE_ID': ['UC_86JXH1', 'UC_WUGAZ7', 'UC_2B0CK2'],
        '!STAGE_ID': ['C1:WON', 'C1:LOSE']
    }
})
tasks = b.get_all('tasks.task.list', {
    'select': ['*', 'UF_*'],
    'filter':
        {'GROUP_ID': '101'}
})

users = b.get_all('user.get')

data = [['Компания', 'Ссылка на компанию', 'Ответственный за компанию', 'Спарк', 'СпаркРиски Плюс', 'Выручка в млн', 'Комментарий']]
for element in revenue_elements:
    company_id = list(element['PROPERTY_1631'].values())[0]
    check_company = list(filter(lambda x: x['ID'] == company_id, companies_info))
    if not check_company:
        continue
    company_name = check_company[0]['TITLE']
    company_responsible_id = check_company[0]['ASSIGNED_BY_ID']
    user_name = list(filter(lambda x: x['ID'] == company_responsible_id, users))[0]
    user_name = f'{user_name["LAST_NAME"]} {user_name["NAME"]}'
    task = list(filter(lambda x: type(x['ufCrmTask']) != bool and 'CO_' + company_id in x['ufCrmTask'], tasks))
    if task:
        responsible_name = task[0]['responsible']['name']
        commentaries = b.get_all('task.commentitem.getlist', {'TASKID': task[0]['id']})
        responsible_commentary = list(filter(lambda x: x['AUTHOR_NAME'] == responsible_name and 'Крайний срок изменен на' not in x['POST_MESSAGE'] and 'Задача завершена' not in x['POST_MESSAGE'], commentaries))
        if responsible_commentary:
            responsible_commentary = responsible_commentary[-1]['POST_MESSAGE']
        else:
            responsible_commentary = ''
    else:
        responsible_commentary = ''

    spark = list(filter(lambda x: x['TYPE_ID'] in ['UC_86JXH1', 'UC_2B0CK2'] and x['COMPANY_ID'] == company_id, deals))
    if spark:
        spark = 'Да'
    else:
        spark = 'Нет'

    spark_plus = list(filter(lambda x: x['TYPE_ID'] == 'UC_WUGAZ7' and x['COMPANY_ID'] == company_id, deals))
    if spark_plus:
        spark_plus = 'Да'
    else:
        spark_plus = 'Нет'

    data.append([
            company_name,
            f'https://vc4dk.bitrix24.ru/crm/company/details/{company_id}/',
            user_name,
            spark,
            spark_plus,
            list(element['PROPERTY_1635'].values())[0],
            responsible_commentary
        ])

workbook = openpyxl.Workbook()
worksheet = workbook.active
for row in data:
    worksheet.append(row)
workbook.save('data.xlsx')

workbook = openpyxl.load_workbook('data.xlsx')
worksheet = workbook.active
for i in range(1, 364):
    cell_value = worksheet['B' + str(i)].value
    worksheet['B' + str(i)].hyperlink = cell_value
    worksheet['B' + str(i)].value = cell_value
    worksheet['B' + str(i)].style = "Hyperlink"
workbook.save('data.xlsx')