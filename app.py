from time import asctime
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

         product_fields = b.get_all('crm.product.get', {'id': product['PRODUCT_ID']})   # Получение полей продукта
         code_1c = product_fields['PROPERTY_139']['value']  # Получение кода 1С
         b.call('crm.deal.update', {'ID': deal_id, 'fields': {'UF_CRM_1655972832': code_1c}})   # Запись кода в сделку

         with open('logs.txt', 'a') as file:
             file.write(f"DEAL_ID: {deal_id} {asctime()}")


     return 'OK'


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)