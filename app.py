from time import asctime
from flask import Flask
from flask import request
import requests


webhook = 'https://vc4dk.bitrix24.ru/rest/311/r1oftpfibric5qym/'

app = Flask(__name__)

log_dct = {}

@app.route('/', methods=['POST', 'HEAD', 'GET'])
def result():
    if request.method == 'GET':
        return log_dct
    else:
        if request.form['event'] == 'ONCRMDEALUPDATE':
            deal_id = request.form['data[FIELDS][ID]']
            if deal_id not in log_dct:
                update_code_1c(deal_id)
        if len(log_dct) > 10:
            log_dct.clear()
        return 'OK'


def update_code_1c(_deal_id):
    deal_id = _deal_id

    # Получение информации о продукте сделки

    deal_product = requests.get(url=webhook + 'crm.deal.productrows.get.json?id=' + deal_id)

    # ID продукта сделки
    try:
        id_deal_product = str(deal_product.json()['result'][0]['PRODUCT_ID'])
    except:
        log_dct.setdefault(deal_id, ['error <id_deal_product>', asctime()])

    # Получение полей продукта

    product_fields = requests.get(url=webhook + 'crm.product.get.json?id=' + id_deal_product)

    # Получение кода 1С

    if product_fields.json()['result']['PROPERTY_139'] is None:
        log_dct.setdefault(deal_id, ['no code', asctime()])
        return 'no code'
    code_1c = product_fields.json()['result']['PROPERTY_139']['value']
    log_dct.setdefault(deal_id, [code_1c, asctime()])

    # Запись кода в сделку

    requests.get(url=f"{webhook}crm.deal.update?id=84621&fields[UF_CRM_1655972832]={code_1c}")
    return f'upd {deal_id}'


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
