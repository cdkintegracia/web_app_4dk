from time import asctime
from flask import Flask
from flask import request
import requests

webhook = 'https://vc4dk.bitrix24.ru/rest/311/r1oftpfibric5qym/'

app = Flask(__name__)


@app.route('/', methods=['POST', 'HEAD', 'GET'])
def result():

    if request.form['event'] == 'ONCRMDEALUPDATE':
        print('ok')
    #print(update_code_1c(request.form))
    else:
        print('neok')
    return 'OK'


def update_code_1c(req):

    deal_id = request.form['data[FIELDS][ID]']

    # Получение информации о продукте сделки

    deal_product = requests.get(
        url=webhook + 'crm.deal.productrows.get.json?id=' + deal_id
    )

    # ID продукта сделки

    id_deal_product = str(deal_product.json()['result'][0]['PRODUCT_ID'])

    # Получение полей продукта

    product_fields = requests.get(url=webhook + 'crm.product.get.json?id=' + id_deal_product)

    # Получение кода 1С

    code_1c = product_fields.json()['result']['PROPERTY_139']['value']

    # Запись кода в сделку

    requests.get(url=f"{webhook}crm.deal.update?id=84621&fields[UF_CRM_1655972832]={code_1c}")

    return 'upd'


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)