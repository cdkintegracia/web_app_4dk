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
    employees = {}  # Dct сотрудников, значения которых - ID сделок для задачи
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

    prof_deals = [
                    'UC_XIYCTV',  # ПРОФ Земля + Помощник
                    'UC_5T4MAW',  # ПРОФ Земля + Облако + Помощник
                    'UC_2SJOEJ',  # ПРОФ Облако+Помощник
                    'UC_92H9MN',  # Индивидуальный
                    'UC_7V8HWF',  # Индивидуальный + Облако
                    'UC_1UPOTU',  # ИТС Бесплатный
                    'UC_DBLSP5',  # Садовод + Помощник
                ]

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

    # начались в сентябре 2022 и заканчиваются после сентября 2022

    deals_start_in_end_after = b.get_all(
        'crm.deal.list', {
            'filter': {
                '>BEGINDATE': date_start,
                '<BEGINDATE': date_end,
                '>CLOSEDATE': date_end,
                'TYPE_ID': prof_deals,
            }
        }
    )

    # начались до сентября 2022 и заканчиваются в сентябре 2022

    deals_start_before_end_in = b.get_all(
        'crm.deal.list', {
            'filter': {
                '<BEGINDATE': date_start,
                '>CLOSEDATE': date_start,
                '<CLOSEDATE': date_end,
                'TYPE_ID': prof_deals,
            }
        }
    )

    # начались до сентября 2022 и заканчиваются после сентября 2022

    deals_start_before_end_after = b.get_all(
        'crm.deal.list', {
            'filter': {
                '<BEGINDATE': date_start,
                '>CLOSEDATE': date_end,
                'TYPE_ID': prof_deals,
            }
        }
    )

    deals = deals_start_before_end_in + deals_start_in_end_after + deals_start_before_end_after

    # Разделение ID сделок по ответственному

    for deal in deals:
        employee = deal['ASSIGNED_BY_ID']   # Ответственный
        if employee not in employees:
            employees.setdefault(employee, [deal['ID'], ])  # Создание ключа с ID сотрудника и значение - ID сделки
        else:
            employees[employee].append(deal['ID'])  # Добавление ID сделки к значению dct

    # Формирование задач

    for employee in employees:
        '''
        Есть сделка без ответственного, после ее удаления - можно удалить try
        '''
        try:
            employee_fields = b.get_all('user.get', {"ID": employee})
            employee_name = employee_fields[0]['NAME'] + ' ' + employee_fields[0]['LAST_NAME']
        except:
            print(employee, employees[employee])
        for tasks_employee in employees:
            print('TASKS', employees[employee])


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

