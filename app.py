from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from TaskService import create_task_service
from UpdateCompanyValue import update_company_value
from UpdateCode1C import update_code_1c
from UpdateCallStatistic import update_call_statistic


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///DataBase.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    goal = db.Column(db.Integer)


# Словарь функций для вызова из кастомного запроса

custom_webhooks = {
    'create_task_service': create_task_service,
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


@app.route('/', methods=['HEAD', 'GET'])
def site():

    return render_template('index.html')


@app.route('/<login>/<password>/<goal>')
def index(login, password, goal):
    user = User(login=login, password=password, goal=goal)
    db.session.add(user)
    db.session.commit()
    return '<h1>New user!</h1>'


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
