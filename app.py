import time
from flask import Flask
from flask import request
import requests
import schedule

webhook = 'https://vc4dk.bitrix24.ru/rest/311/r1oftpfibric5qym/'

app = Flask(__name__)

log_dct = {}

@app.route('/', methods=['POST', 'HEAD'])
def result():

    if request.form['event'] == 'ONCRMDEALUPDATE':
        deal_id = request.form['data[FIELDS][ID]']
        if deal_id not in log_dct:
            update_code_1c(deal_id)
    print(log_dct)
    return 'OK'


def update_code_1c(_deal_id):
    deal_id = _deal_id

    # Получение информации о продукте сделки

    deal_product = requests.get(url=webhook + 'crm.deal.productrows.get.json?id=' + deal_id)

    # ID продукта сделки
    print(deal_product.json())
    id_deal_product = str(deal_product.json()['result'][0]['PRODUCT_ID'])

    # Получение полей продукта

    product_fields = requests.get(url=webhook + 'crm.product.get.json?id=' + id_deal_product)

    # Получение кода 1С

    if product_fields.json()['result']['PROPERTY_139'] is None:
        log_dct.setdefault(deal_id, 'no code')
        return 'no code'
    code_1c = product_fields.json()['result']['PROPERTY_139']['value']
    log_dct.setdefault(deal_id, code_1c)

    # Запись кода в сделку

    requests.get(url=f"{webhook}crm.deal.update?id=84621&fields[UF_CRM_1655972832]={code_1c}")

    time.sleep(5)
    return f'upd {deal_id}'


def clear_temp_list():
    global log_dct
    log_dct.clear()
    print(f'log_dct is empty {log_dct}')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)


schedule.every().day.at("16:00").do(clear_temp_list)


while True:
    schedule.run_pending()