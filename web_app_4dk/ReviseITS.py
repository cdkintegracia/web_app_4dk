from time import strftime

import requests
import gspread
from fast_bitrix24 import Bitrix

from web_app_4dk.authentication import authentication

b = Bitrix(authentication('Bitrix'))

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

eng_month_string = {
    'Jan': '01',
    'Feb': '02',
    'Mar': '03',
    'Apr': '04',
    'May': '05',
    'Jun': '06',
    'Jul': '07',
    'Aug': '08',
    'Sep': '09',
    'Oct': '10',
    'Nov': '11',
    'Dec': '12',
}

stage_string = {
    'C1:LOSE': 'Отказ от сопровождения',
    'C1:NEW': 'Услуга активна',
    'C1:UC_0KJKTY': 'Счет сформирован',
    'C1:UC_3J0IH6': 'Счет отправлен клиенту',
    'C1:UC_KZSOR2': 'Нет оплаты',
    'C1:UC_VQ5HJD': 'Ждём решения клиента',
    'C1:WON': 'Услуга завершена',
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
                  'Стадия сделки',
                  'Найдено соответствие',
                  'ДК в АПИ',
                  'Дополнительная информация']]

    deals = b.get_all('crm.deal.list', {
        'select': [
            'UF_CRM_1640523562691',     # Регномер
            'UF_CRM_1655972832',        # СлужКод1с
            'CLOSEDATE',                # ДК
            'COMPANY_ID',               # ID компании
            'STAGE_ID',                 # Стадия сделки
        ],
        'filter': {
            'TYPE_ID': [
                'UC_HT9G9H',    # ПРОФ Земля
                'UC_XIYCTV',    # ПРОФ Земля+Помощник
                #'UC_N113M9',    # ПРОФ Земля+Облако
                #'UC_5T4MAW',    # ПРОФ Земля+Облако+Помощник
                'UC_AVBW73',    # Базовый Земля
                'UC_81T8ZR',    # АОВ
                'UC_92H9MN',    # Индивидуальный
                'UC_1UPOTU',    # ИТС Бесплатный
                'UC_K9QJDV',    # ГРМ Бизнес
                'GOODS',        # ГРМ
                #'UC_J426ZW',    # Садовод
                'UC_DBLSP5',    # Садовод+Помощник
                #'UC_BZYY0D',    # ИТС Отраслевой
            ],
            '!CLOSEDATE': current_date,
            '>CLOSEDATE': current_date,
            '!UF_CRM_1655972832': None,
            '!UF_CRM_1640523562691': None,
        }
    }
                      )
    errors = []
    for deal in deals:
        accordance = ''
        date_end_api = ''
        extend_info = ''
        date_end_b24 = deal['CLOSEDATE'][:10].split('-')
        date_end_b24 = f"{date_end_b24[2]}.{date_end_b24[1]}.{date_end_b24[0]}"
        try:
            company_name = b.get_all('crm.company.list', {
                'select': ['TITLE'],
                'filter': {'ID': deal['COMPANY_ID']}})[0]['TITLE']
        except:
            company_name = ''
        request_data = send_request(deal['UF_CRM_1640523562691'])
        for data in request_data:

            try:
                # Заполнение 'Найдено соответствие '
                for itsContractInfo in data['itsContractInfo']:

                    # Найден
                    if 'Договор оформлен вашей организацией' in itsContractInfo['description'] \
                            and ((str(itsContractInfo['itsContractType']['publicSubscriptionTypeNumber']) == deal['UF_CRM_1655972832']) or
                                 (str(itsContractInfo['itsContractType']['publicSubscriptionTypeNumber']) == '130' and deal['UF_CRM_1655972832'] in ['131', '133'])):
                        accordance = 'Найден'
                        date_end_api = itsContractInfo['endDate'].split()
                        date_end_api = f"{date_end_api[2]}.{eng_month_string[date_end_api[1]]}.{date_end_api[-1]}"

                    # Расхождение (нет такого кода)
                    elif 'Договор оформлен вашей организацией' in itsContractInfo['description'] and \
                          str(itsContractInfo['itsContractType']['publicSubscriptionTypeNumber']) != deal['UF_CRM_1655972832']\
                            and accordance != 'Найден':
                        accordance = 'Расхождение (нет такого кода)'
                        extend_info += f"{itsContractInfo['itsContractType']['publicSubscriptionTypeNumber']}" \
                                       f" {itsContractInfo['description']}; "

                    # Расхождение (договор у другого партнера)
                    elif 'Договор оформлен другим партнером' in itsContractInfo['description'] \
                            and accordance != 'Найден' and accordance != 'Расхождение (нет такого кода)' \
                            and str(itsContractInfo['itsContractType']['publicSubscriptionTypeNumber']) == deal['UF_CRM_1655972832']:
                        accordance = 'Расхождение (договор у другого партнера)'
                        extend_info += f"{itsContractInfo['itsContractType']['publicSubscriptionTypeNumber']}" \
                                       f" {itsContractInfo['description']}; "

            except:
                if f"{deal['ID']} {deal['UF_CRM_1640523562691']}" not in errors:
                    errors.append(f"{deal['ID']} {deal['UF_CRM_1640523562691']}")

            if accordance == '':
                accordance = 'Отсутствует'

        data_list.append([
            deal['UF_CRM_1640523562691'],   # Регномер в Б24
            deal['UF_CRM_1655972832'],      # Код в Б24
            company_name,                   # Название Компании в Б24
            date_end_b24,                   # ДК сделки в Б24
            stage_string[deal['STAGE_ID']], # Стадия сделки
            accordance,                     # Найдено соответствие
            date_end_api,                   # ДК в АПИ
            extend_info,                    # Дополнительная информация
        ]
        )

    """
    Google sheets
    """

    access = gspread.service_account(f"/root/credentials/bitrix24-data-studio-2278c7bfb1a7.json")
    spreadsheet = access.open('Сверка ИТС')
    try:
        worksheet = spreadsheet.add_worksheet(title=worksheet_date, rows=1, cols=1)
    except gspread.exceptions.APIError:
        worksheet = spreadsheet.worksheet(worksheet_date)

    worksheet.clear()
    worksheet.update('A1', data_list)

    if len(errors) == 0:
        b.call('im.notify.system.add', {'USER_ID': req['user_id'][5:], 'MESSAGE': f'Сверка ИТС завершена. Ссылка на файл: '
                                                                         f'https://docs.google.com/spreadsheets/d/1vW7u2HhetM6P5FDR9_AWEiwHY9ef-30RdG2i1Tm-C0w/edit#gid=934883478'})
    else:
        b.call('im.notify.system.add',
               {'USER_ID': req['user_id'][5:], 'MESSAGE': f'Сверка ИТС завершена. Ссылка на файл: '
                                                          f'https://docs.google.com/spreadsheets/d/1vW7u2HhetM6P5FDR9_AWEiwHY9ef-30RdG2i1Tm-C0w/edit#gid=934883478'
                                                          f'Ошибочные сделки (ID Регномер): '
                                                          f'{errors}'})