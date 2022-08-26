from flask import Flask, request, render_template

from web_app_4dk.TaskService import create_task_service
from web_app_4dk.UpdateCompanyValue import update_company_value
from web_app_4dk.UpdateCode1C import update_code_1c
from web_app_4dk.UpdateCallStatistic import update_call_statistic
from web_app_4dk.CheckTaskResult import check_task_result


app = Flask(__name__)


# Словарь функций для вызова из кастомного запроса

custom_webhooks = {
    'create_task_service': create_task_service,
    'check_task_result': check_task_result,
}

# Словарь функций для вызова из запроса с стандартным методом

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



if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
