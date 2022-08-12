from time import asctime
from flask import Flask
from flask import request
import requests


webhook = 'https://vc4dk.bitrix24.ru/rest/311/r1oftpfibric5qym/'

app = Flask(__name__)

logs = []


@app.route('/', methods=['POST', 'HEAD', 'GET'])
def result():
    if request.method == 'POST':
        if 'create_service_tasks' in request:
            print('Подходит')
            return 'ura'
        else:
            print('Не подходит', request)
            return 'oke'
    else:
        return 'OK'


if __name__ == '__main__':
    app.run(host='0.0.0.0')