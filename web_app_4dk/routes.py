from time import asctime

from flask import request, render_template
from flask_login import LoginManager

from web_app_4dk import app, db
from web_app_4dk.models import UserAuth
from web_app_4dk.modules.TaskService import create_task_service
from web_app_4dk.modules.UpdateCompanyValue import update_company_value
from web_app_4dk.modules.UpdateCode1C import update_code_1c
from web_app_4dk.modules.UpdateCallStatistic import update_call_statistic
from web_app_4dk.modules.CheckTaskResult import check_task_result
from web_app_4dk.modules.ReviseITS import revise_its
from web_app_4dk.modules.Prolongation_ITS import prolongation_its
from web_app_4dk.modules.CreateDeal import create_deal
from web_app_4dk.modules.Connect1C import connect_1c
from web_app_4dk.modules.UpdateUserStatistics import update_user_statistics
from web_app_4dk.modules.UpdateContactPhoto import update_contact_photo
from web_app_4dk.modules.RewriteCallStatistic import rewrite_call_statistic


# Словарь функций для вызова из кастомного запроса

custom_webhooks = {
    'create_task_service': create_task_service,
    'check_task_result': check_task_result,
    'revise_its': revise_its,
    'prolongation_its': prolongation_its,
}

# Словарь функций для вызова из запроса со стандартным методом

default_webhooks = {
    'ONCRMDEALUPDATE': update_code_1c,
    'ONCRMDEALDELETE': update_company_value,
    'ONVOXIMPLANTCALLEND': update_call_statistic,
    'ONCRMDEALADD': create_deal,
    'ONCRMACTIVITYADD': update_user_statistics,
    'ONTASKADD': update_user_statistics,
    'ONTASKUPDATE': update_user_statistics,
    'ONCRMCONTACTUPDATE': update_contact_photo,
}

# Обработчик стандартных вебхуков Битрикс

@app.route('/bitrix/default_webhook', methods=['POST', 'HEAD'])
def default_webhook():
    update_logs("Получен дефолтный вебхук", request.form)
    default_webhooks[request.form['event']](request.form)
    return 'OK'

# Обработчик кастомных вебхуков Битрикс

@app.route('/create', methods=['GET'])
def create():
    c = UserAuth(login='login', password='12345')

@app.route('/bitrix/custom_webhook', methods=['POST', 'HEAD'])
def custom_webhook():
    update_logs("Получен кастомный вебхук", request.args)
    job = request.args['job']
    custom_webhooks[job](request.args)
    return 'OK'


@app.route('/', methods=['GET', 'POST'])
def main_page():
    try:
        if request.method == 'POST':
            new_call_statistic_file = request.files['new_call_statistic_file']
            new_call_statistic_file.save('/root/web_app_4dk/web_app_4dk/new_call_statistic.xlsx')
            month = request.form.get('month')
            year = request.form.get('year')
            rewrite_call_statistic(month, year)
    except:
        pass
    return render_template('main_page.html', web_app_logs=read_logs())

# Обработчик вебхуков 1С-Коннект

@app.route('/1c-connect', methods=['POST'])
def update_connect_logs():
    update_logs("Получен 1С-Коннект вебхук", request.json)
    connect_1c(request.json)
    return 'OK'

# Обновление логов веб-приложения
def update_logs(text, req):
    log_dct = {}
    for key in req:
        log_dct.setdefault(key, req[key])
    with open('logs.txt', 'a') as log_file:
        log_file.write(f"{asctime()} | {text} | request: {log_dct}\n")


# Вывод на экран логов веб-приложения
def read_logs():
    final_text = []
    with open('logs.txt', 'r') as log_file:
        logs = log_file.readlines()
        for s in logs:
            info_text = s.split('request: ')[0]
            request_text = s.split('request: ')[1]
            request_text = request_text.split(',')
            final_text.append([info_text, request_text])
        return final_text[::-1]