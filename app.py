import requests
import json
from flask import Flask
from flask import request

app = Flask(__name__)


@app.route('/', methods=['POST'])
def result():
     print(request.form)
     return 'OK'


if __name__ == '__main__':
    app.run()