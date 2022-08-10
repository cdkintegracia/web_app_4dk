import requests
import json
from flask import Flask
from flask import request
from fast_bitrix24 import Bitrix

webhook = 'https://vc4dk.bitrix24.ru/rest/311/r1oftpfibric5qym/'
b = Bitrix(webhook)

app = Flask(__name__)


@app.route('/', methods=['POST', 'HEAD', 'GET'])
def result():
     deal_id = request.form['data[FIELDS][ID]']     # ID из POST запроса
     products = b.get_all('crm.deal.productrows.get', {'id': deal_id})    # Получение информации о продукте сделки
     for product in products:
         pr = b.get_all('crm.product.get', {'id': product['PRODUCT_ID']})
         print(pr)
     return 'OK'


if __name__ == '__main__':
    app.run(host='0.0.0.0')