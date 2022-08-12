from time import asctime
from flask import Flask
from flask import request
import requests


webhook = 'https://vc4dk.bitrix24.ru/rest/311/r1oftpfibric5qym/'

app = Flask(__name__)


def create_task_service():
    print('поехали')




custom_webhooks = {'create_task_service': create_task_service}

@app.route('/', methods=['POST', 'HEAD', 'GET'])
def result():
    if request.method == 'POST':
        if 'create_task_service' in request.url:
            if 'job' in request.args:
                job = request.args['job']
                custom_webhooks[job]()
                return 'OK'
        return 'OK'
    else:
        return 'OK'


if __name__ == '__main__':
    app.run(host='0.0.0.0')

