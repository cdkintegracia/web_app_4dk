from flask import Flask, request, render_template
from TaskService import create_task_service
from UpdateCompanyValue import update_company_value
from UpdateCode1C import update_code_1c
from UpdateCallStatistic import update_call_statistic


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.sqlite3'


# Словарь возможных функций для вызова из кастомного запроса

custom_webhooks = {'create_task_service': create_task_service}

# Обработчик стандартных вебхуков Битрикс

@app.route('/bitrix/default_webhook', methods=['POST', 'HEAD'])
def default_webhook():
    if request.form['event'] == 'ONCRMDEALUPDATE':
        deal_id = request.form['data[FIELDS][ID]']
        update_code_1c(deal_id)
        return 'OK'
    elif request.form['event'] == 'ONCRMDEALDELETE':
        deal_id = request.form['data[FIELDS][ID]']
        update_company_value(deal_id)
    elif request.form['event'] == 'ONVOXIMPLANTCALLEND':
        client_number = request.form['data[PHONE_NUMBER]']
        employee_number = request.form['data[PORTAL_NUMBER]']
        print(client_number, employee_number)
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
