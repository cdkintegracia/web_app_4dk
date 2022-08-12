from time import asctime
from flask import Flask
from flask import request
import requests
from fast_bitrix24 import Bitrix
from calendar import monthrange


webhook = 'https://vc4dk.bitrix24.ru/rest/311/r1oftpfibric5qym/'
b = Bitrix(webhook)

app = Flask(__name__)


def create_task_service(dct):
    months = {
        'Январь': 1,
        'Февраль': 2,
        'Март': 3,
        'Апрель': 4,
        'Май': 5,
        'Июнь': 6,
        'Июль': 7,
        'Август': 8,
        'Сентябрь': 9,
        'Октябрь': 10,
        'Ноябрь': 11,
        'Декабрь': 12
    }
    month = months[dct['month']]
    year = dct['year']
    date_start = f'01-0{month}-{year}'
    print(date_start)
    #deals = b.get_all('crm.deal.list')



# Словарь возможных функций для вызова из кастомного запроса
custom_webhooks = {'create_task_service': create_task_service}



@app.route('/', methods=['POST', 'HEAD', 'GET'])
def result():
    if request.method == 'POST':
        if 'create_task_service' in request.url:
            if 'job' in request.args:
                job = request.args['job']
                custom_webhooks[job](request.args)
                return 'OK'
        return 'OK'
    else:
        return 'OK'


if __name__ == '__main__':
    app.run(host='0.0.0.0')

