from authentication import authentication
from fast_bitrix24 import Bitrix
import requests
from time import asctime

# Считывание файла authentication.txt

webhook = authentication('Bitrix')
b = Bitrix(webhook)

logs = []

def update_code_1c(req):
    """
    :param req: request.form
    :return: Заполнение или обновление поля "Код1С" в сделке
    """
    deal_id = req['data[FIELDS][ID]']
    global logs

    # Получение информации о продукте сделки

    deal_product = requests.get(url=webhook + 'crm.deal.productrows.get.json?id=' + deal_id)

    # ID продукта сделки
    try:
        id_deal_product = str(deal_product.json()['result'][0]['PRODUCT_ID'])
    except:
        log = f'ERROR: DEAL: {deal_id} | {asctime()}'
        if log not in logs:
            logs.append(log)

    # Получение полей продукта

    product_fields = requests.get(url=webhook + 'crm.product.get.json?id=' + id_deal_product)

    # Получение кода 1С

    if product_fields.json()['result']['PROPERTY_139'] is None:
        log = f'NO CODE: DEAL: {deal_id} | {asctime()}'
        if log not in logs:
            logs.append(log)
        return "NO CODE"
    code_1c = product_fields.json()['result']['PROPERTY_139']['value']

    # Сверка кода 1С продукта и кода в сделке

    deal_1c_code = requests.get(url=f"{webhook}crm.deal.get?id={deal_id}").json()['result']['UF_CRM_1655972832']

    if deal_1c_code != code_1c:

        # Запись кода в сделку

        requests.post(url=f"{webhook}crm.deal.update?id={deal_id}&fields[UF_CRM_1655972832]={code_1c}")
        log = f'UPD: DEAL: {deal_id} | OLD_CODE: {deal_1c_code} | NEW_CODE: {code_1c} | {asctime()}'
        if log not in logs:
            logs.append(log)
        return 'UPD'