from flask import Flask, request, render_template
from time import asctime

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
    update_logs("Получен дефолтный вебхук", request.form)
    default_webhooks[request.form['event']](request.form)
    return 'OK'

# Обработчик кастомных вебхуков Битрикс

@app.route('/bitrix/custom_webhook', methods=['POST', 'HEAD'])
def custom_webhook():
    update_logs("Получен кастомный вебхук", request.form)
    job = request.args['job']
    custom_webhooks[job](request.args)
    return 'OK'


@app.route('/', methods=['GET'])
def main_page():
    return render_template('main_page.html', web_app_logs=read_logs())


def update_logs(text, req):
    log_dct = {}
    for key in req:
        log_dct.setdefault(key, req[key])
    with open('logs.txt', 'a') as log_file:
        log_file.write(f"{asctime()} | {text} | request: {log_dct}\n")


def read_logs():
    final_text = []
    with open('logs.txt', 'r') as log_file:
        logs = log_file.readlines()
        for s in logs:
            info_text = s.split('request: ')[0]
            request_text = s.split('request: ')[1]
            request_text.split(',')
            final_text.append([info_text, request_text])
        return final_text[::-1]


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
