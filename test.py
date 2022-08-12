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
        if 'create_task_service':
            print('Подходит', request)
            print(request.data)
            print(request.url)
        return 'OK'
    else:
        return 'OK'

def create_task_service():
    pass


if __name__ == '__main__':
    app.run(host='0.0.0.0')

