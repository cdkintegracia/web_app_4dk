from fast_bitrix24 import Bitrix
import openpyxl

#from web_app_4dk.modules.authentication import authentication


# Считывание файла authentication.txt

#webhook = authentication('Bitrix')
webhook = 'https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/'
b = Bitrix(webhook)

def create_report_rpd():
    stage_names = {
        'C13:NEW': 'Новые',
        'C13:UC_PYAKJ0': 'Отправлено письмо / сообщение',
        'C13:PREPAYMENT_INVOIC': 'Презентация (телефон / лично)',
        'C13:UC_T4D1BX': 'Не хотят слушать',
        'C13:EXECUTING': 'Тестовый пакет',
        'C13:FINAL_INVOICE': 'В рамках ИТС',
        'C13:UC_CI976X': 'Выставлен счет',
        'C13:LOSE': 'Отказ',
        'C13:WON': 'Оплачен счет',
    }
    result_dict = {}
    deals = b.get_all('crm.deal.list', {'select': ['ASSIGNED_BY_ID', 'STAGE_ID'], 'filter': {'CATEGORY_ID': '13'}})
    for deal in deals:
        worker = deal['ASSIGNED_BY_ID']
        stage = deal['STAGE_ID']
        if worker not in result_dict:
            result_dict.setdefault(worker, {stage: 1})
        else:
            if stage not in result_dict[worker]:
                result_dict[worker].setdefault(stage, 1)
            else:
                result_dict[worker][stage] += 1
    for worker in result_dict.items():
        print(i)


create_report_rpd()