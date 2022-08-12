from time import asctime
from flask import Flask
from flask import request
import requests
from fast_bitrix24 import Bitrix
from calendar import monthrange


webhook = 'https://vc4dk.bitrix24.ru/rest/311/r1oftpfibric5qym/'
b = Bitrix(webhook)

app = Flask(__name__)


def create_task_service(dct):
    """
    :param dct: Словарь из url POST запроса, в котором есть ключи 'year', 'month'
    :return: Создает задачи
    """
    months = {
        'Январь': 1,
        'Февраль': 2,
        'Март': 3,
        'Апрель': 4,
        'Май': 5,
        'Июнь': 6,
        'Июль': 7,
        'Август': 8,
        'Сентябрь': 9,
        'Октябрь': 10,
        'Ноябрь': 11,
        'Декабрь': 12
    }

    year = int(dct['year'])
    month = str(months[dct['month']])   # Месяц из параметра, преобразованный в число
    month_end = str(months[dct['month']] + 1)   # Месяц начала фильтрации
    if month == '1':    # Месяц конца фильтрации
        month_start = '12'  # Если месяц январь, то предыдущий - декабрь
    else:
        month_start = str(months[dct['month']] - 1)
    day_start = monthrange(year, int(month_start))[1]   # День начала фильтрации

    if len(month_start) == 1:     # Если месяц состоит из одной цифры, тогда он приводится к двухзначному формату
        month_start = '0' + month_start
    if len(month_end) == 1:
        month_end = '0' + month_end    # Если месяц состоит из одной цифры, тогда он приводится к двухзначному формату

    date_start = f'{year}-{month_start}-{day_start}'
    date_end = f'{year}-{month_end}-01'

    deals = b.get_all(
        'crm.deal.list', {
            'filter': {
                '>BEGINDATE': date_start,
                '<BEGINDATE': date_end,
                '>CLOSEDATE': date_start,
                '<CLOSEDATE': date_end,
            }
        }
    )
    for deal in deals:
        print(deal['BEGINDATE'], deal['CLOSEDATE'])



# Словарь возможных функций для вызова из кастомного запроса
custom_webhooks = {'create_task_service': create_task_service}



@app.route('/', methods=['POST', 'HEAD', 'GET'])
def result():
    if request.method == 'POST':
        if 'create_task_service' in request.url:
            if 'job' in request.args:
                job = request.args['job']
                custom_webhooks[job](request.args)
                return 'OK'
        return 'OK'
    else:
        return 'OK'


if __name__ == '__main__':
    app.run(host='0.0.0.0')

