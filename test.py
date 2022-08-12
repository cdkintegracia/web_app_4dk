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
        url_data = request.data.decode()
        if 'create_service_tasks' in url_data:
            return url_data
        else:
            return 'oke'
    else:
        return 'OK'


if __name__ == '__main__':
    app.run(host='0.0.0.0')