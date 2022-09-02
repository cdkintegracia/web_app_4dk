from time import strftime

import requests
import gspread
from fast_bitrix24 import Bitrix
'''
from authentication import authentication

b = Bitrix(authentication('Bitrix'))
'''

b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')

month_string = {
        '01': 'Январь',
        '02': 'Февраль',
        '03': 'Март',
        '04': 'Апрель',
        '05': 'Май',
        '06': 'Июнь',
        '07': 'Июль',
        '08': 'Август',
        '09': 'Сентябрь',
        '10': 'Октябрь',
        '11': 'Ноябрь',
        '12': 'Декабрь'
    }


current_day = strftime('%d')
current_month = month_string[strftime('%m')]
current_year = strftime('%y')
worksheet_date = f"{current_day} {current_month} {current_year}"

def send_request(regnumber):

    headers = {
        'accept': 'application/json;charset=UTF-8',
        'Content-Type': 'application/json;charset=UTF-8',
        'Authorization': 'Basic YXBpLWxvZ2luLTQzODI6MGY4M2VmYWQwODEzNGM='  # Логин:пароль в base64
    }

    json_data = {
        'regNumberList': [
            regnumber,
        ],
    }

    response = requests.post('https://partner-api.1c.ru/api/rest/public/subscription /checkItsByRegNum',
                             headers=headers, json=json_data)

    return response.json()

def revise_its(req):
    """
    :param
    :return: Создание excel файла с сверкой
    """
    current_date = strftime('%Y-%m-%d')
    data_list = [['Регномер в Б24',
                  'Код в Б24',
                  'Название Компании в Б24',
                  'ДК сделки в Б24',
                  'Найдено соответствие',
                  'ДК в АПИ',
                  'Дополнительная информация']]

    deals = b.get_all('crm.deal.list', {
        'select': [
            'UF_CRM_1640523562691',     # Регномер
            'UF_CRM_1655972832',        # СлужКод1с
            'CLOSEDATE',                # ДК
            'COMPANY_ID',               # ID компании
        ],
        'filter': {
            'TYPE_ID': [
                'UC_HT9G9H',    # ПРОФ Земля
                'UC_XIYCTV',    # ПРОФ Земля+Помощник
                'UC_N113M9',    # ПРОФ Земля+Облако
                'UC_5T4MAW',    # ПРОФ Земля+Облако+Помощник
                'UC_AVBW73',    # Базовый Земля
                'UC_81T8ZR',    # АОВ
                'UC_92H9MN',    # Индивидуальный
                'UC_1UPOTU',    # ИТС Бесплатный
                'UC_K9QJDV',    # ГРМ Бизнес
                'GOODS',        # ГРМ
                'UC_J426ZW',    # Садовод
                'UC_DBLSP5',    # Садовод+Помощник
                'UC_BZYY0D',    # ИТС Отраслевой
            ],
            '!CLOSEDATE': current_date,
            '>CLOSEDATE': current_date,
            '!UF_CRM_1655972832': None,
            '!UF_CRM_1640523562691': None,
        }
    }
                      )
    for deal in deals:
        company_name = b.get_all('crm.company.list', {
            'select': ['TITLE'],
            'filter': {'ID': deal['COMPANY_ID']}})[0]['TITLE']
        request_data = send_request(deal['UF_CRM_1640523562691'])
        for data in request_data:
            for itsContractInfo in data['itsContractInfo']:
                print(itsContractInfo)
                exit()

        data_list.append([
            deal['UF_CRM_1640523562691'],   # Регномер в Б24
            deal['UF_CRM_1655972832'],      # Код в Б24
            company_name,                   # Название Компании в Б24
            deal['CLOSEDATE'],              # ДК сделки в Б24
            1,                              # Найдено соответствие
            'req_end'                       # ДК в АПИ
            'test'                          # Дополнительная информация
        ]
        )
        break

    """
    Google sheets
    """

    access = gspread.service_account(filename='bitrix24-data-studio-2278c7bfb1a7.json')
    spreadsheet = access.open('Сверка ИТС')
    try:
        worksheet = spreadsheet.add_worksheet(title=worksheet_date, rows=1, cols=1)
    except gspread.exceptions.APIError:
        worksheet = spreadsheet.worksheet(worksheet_date)

    worksheet.clear()
    worksheet.update('A1', data_list)


if __name__ == '__main__':
    revise_its(1)


