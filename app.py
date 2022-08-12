from time import asctime
from flask import Flask
from flask import request
import requests


webhook = 'https://vc4dk.bitrix24.ru/rest/311/r1oftpfibric5qym/'

app = Flask(__name__)

logs = []

@app.route('/', methods=['POST', 'HEAD', 'GET'])
def result():
    if request.method == 'GET':
        for log in logs:
            print(log)
            return logs
    else:
        if request.form['event'] == 'ONCRMDEALUPDATE':
            deal_id = request.form['data[FIELDS][ID]']
            update_code_1c(deal_id)
        return 'OK'


def update_code_1c(_deal_id):
    global logs
    deal_id = _deal_id

    # Получение информации о продукте сделки

    deal_product = requests.get(url=webhook + 'crm.deal.productrows.get.json?id=' + deal_id)

    # ID продукта сделки
    try:
        id_deal_product = str(deal_product.json()['result'][0]['PRODUCT_ID'])
    except:
        logs.append(f'ERROR: DEAL: {deal_id} {asctime()}')

    # Получение полей продукта

    product_fields = requests.get(url=webhook + 'crm.product.get.json?id=' + id_deal_product)

    # Получение кода 1С

    if product_fields.json()['result']['PROPERTY_139'] is None:
        logs.append(f'NO CODE: DEAL: {deal_id} {asctime()}')
        return "NO CODE"
    code_1c = product_fields.json()['result']['PROPERTY_139']['value']

    # Сверка кода 1С продукта и кода в сделке

    deal_1c_code = requests.get(url=f"{webhook}crm.deal.get?id=95441").json()['result']['UF_CRM_1655972832']
    if deal_1c_code != code_1c:

        # Запись кода в сделку

        requests.post(url=f"{webhook}crm.deal.update?id={deal_id}&fields[UF_CRM_1655972832]={code_1c}")
        logs.append(f'UPD: DEAL: {deal_id} OLD_CODE: {deal_1c_code} NEW_CODE: {code_1c} {asctime()}')
        return 'UPD'


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
