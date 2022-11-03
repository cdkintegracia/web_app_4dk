from calendar import monthrange

from fast_bitrix24 import Bitrix

#from web_app_4dk.modules.authentication import authentication


# Считывание файла authentication.txt

#webhook = authentication('Bitrix')
webhook = 'https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/'
b = Bitrix(webhook)


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


def create_line_consultation_report(req):
    month_codes = {
        'Январь': '01',
        'Февраль': '02',
        'Март': '03',
        'Апрель': '04',
        'Май': '05',
        'Июнь': '06',
        'Июль': '07',
        'Август': '08',
        'Сентябрь': '09',
        'Октябрь': '10',
        'Ноябрь': '11',
        'Декабрь': '12'
    }
    #filter_date = f"{req['year']}-{month_codes[req['month']]}-01"

    deals = b.get_all('crm.deal.list', {
        'filter': {
            'UF_CRM_1657878818384': '859',   # ИТС
            }})
    data_to_write = []
    ignore_list = []
    for deal in deals:
        company_id = deal['COMPANY_ID']
        company_deals = b.get_all('crm.deal.list', {'filter': {'COMPANY_ID': company_id}})
        for company_deal in company_deals:
            company_deal_id = company_deal['ID']
            company_deal_info = b.get_all('crm.deal.get', {'ID': company_deal_id})
            print(company_deal_info)
            exit()

create_line_consultation_report('req')