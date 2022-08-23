from flask import Flask, request, render_template
from TaskService import create_task_service
from UpdateCompanyValue import update_company_value
from UpdateCode1C import update_code_1c
from UpdateCallStatistic import update_call_statistic


app = Flask(__name__)


# Словарь возможных функций для вызова из кастомного запроса

custom_webhooks = {
    'create_task_service': create_task_service,
}
default_webhooks = {
    'ONCRMDEALUPDATE': update_code_1c,
    'ONCRMDEALDELETE': update_company_value,
    'ONVOXIMPLANTCALLEND': update_call_statistic,
}

# Обработчик стандартных вебхуков Битрикс

@app.route('/bitrix/default_webhook', methods=['POST', 'HEAD'])
def default_webhook():
    default_webhooks[request.form['event']](request.form)
    return 'OK'


# Обработчик кастомных вебхуков Битрикс

@app.route('/bitrix/custom_webhook', methods=['POST', 'HEAD'])
def custom_webhook():
    job = request.args['job']
    custom_webhooks[job](request.args)
    return 'OK'


@app.route('/', methods=['HEAD', 'GET'])
def site():
    return render_template('index.html')



if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
