import time
from flask import Flask
from flask import request
import requests
import schedule

webhook = 'https://vc4dk.bitrix24.ru/rest/311/r1oftpfibric5qym/'

app = Flask(__name__)

temp_list = []

@app.route('/', methods=['POST', 'HEAD'])
def result():

    if request.form['event'] == 'ONCRMDEALUPDATE':
        if request.form['data[FIELDS][ID]'] not in temp_list:
            temp_list.append(request.form['data[FIELDS][ID]'])
            update_code_1c(request.form['data[FIELDS][ID]'])
    print(temp_list)
    return 'OK'


def update_code_1c(_deal_id):
    deal_id = _deal_id

    # Получение информации о продукте сделки

    deal_product = requests.get(url=webhook + 'crm.deal.productrows.get.json?id=' + deal_id)

    # ID продукта сделки

    id_deal_product = str(deal_product.json()['result'][0]['PRODUCT_ID'])

    # Получение полей продукта

    product_fields = requests.get(url=webhook + 'crm.product.get.json?id=' + id_deal_product)
    print(product_fields.json())

    # Получение кода 1С

    code_1c = product_fields.json()['result']['PROPERTY_139']['value']

    # Запись кода в сделку

    requests.get(url=f"{webhook}crm.deal.update?id=84621&fields[UF_CRM_1655972832]={code_1c}")

    time.sleep(5)
    return f'upd {deal_id}'


def clear_temp_list():
    global temp_list
    temp_list = []

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)


schedule.every().day.at("16:00").do(clear_temp_list)


while True:
    schedule.run_pending()