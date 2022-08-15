from time import asctime
from flask import Flask
from flask import request
import requests
from calendar import monthrange
from fast_bitrix24 import Bitrix


webhook = 'https://vc4dk.bitrix24.ru/rest/311/r1oftpfibric5qym/'
b = Bitrix(webhook)

app = Flask(__name__)

logs = []


def create_task_service(dct):
    """
    :param dct: Словарь из url POST запроса, в котором есть ключи 'year', 'month'
    :return: Создает задачи "Сервисный выезд" для сделок уровня ПРОФ для выбранного диапазона дат и с чек-листами,
    где каждый пункт в виде <Название компании> <Название сделки>
    Выборка по датам если выбран сентябрь:

    начались до сентября 2022 и заканчиваются после сентября 2022

    начались в сентябре 2022 и заканчиваются после сентября 2022

    начались до сентября 2022 и заканчиваются в сентябре 2022

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
    current_month_days = monthrange(year, int(month))[1]    # Количество дней в выбранном месяце

    if len(month_start) == 1:     # Если месяц состоит из одной цифры, тогда он приводится к двухзначному формату
        month_start = '0' + month_start
    if len(month_end) == 1:
        month_end = '0' + month_end    # Если месяц состоит из одной цифры, тогда он приводится к двухзначному формату
    if len(month) == 1:  # Если месяц состоит из одной цифры, тогда он приводится к двухзначному формату
        month = '0' + month

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

            # Создание ключа с ID сотрудника и значение:
            # 0: ID сделки
            # 1: Название сделки
            # 2: ID компании
            employees.setdefault(employee, [[deal['ID'], deal['TITLE'], deal['COMPANY_ID']]])
        else:
            # Добавление ID сделки к значению dct
            employees[employee].append([deal['ID'], deal['TITLE'], deal['COMPANY_ID']])

    # Формирование задач

    for employee in employees:
        '''
        Есть сделка без ответственного, после ее удаления - можно удалить try
        '''
        try:
            employee_fields = b.get_all('user.get', {"ID": employee})
            employee_name = employee_fields[0]['NAME'] + ' ' + employee_fields[0]['LAST_NAME']
        except:
            print('ERROR: ', employee, employees[employee])

        task = b.call('tasks.task.add', {
            'fields': {
                'TITLE': f"Сервисный выезд {employee_name} {dct['month']}",
                'DEADLINE': f"{str(year)}-{month}-{current_month_days} 19:00:00",
                'RESPONSIBLE_ID': '311',
                'ALLOW_CHANGE_DEADLINE': 'N',

            }
        }
                      )

        # Перебор значений выбранного выше ключа

        for value in employees[employee]:

            """
            Можно потом удалить проверку на None
            """

            if employee in [None, 'None']:
                continue

            # Создание пунктов чек-листы для созданной задачи на сотрудника

            company = b.get_all('crm.company.list', {
                'filter': {
                    'ID': value[2]
                }
            })

            b.call('task.checklistitem.add', [
                task['task']['id'], {
                    'TITLE': f"{company[0]['TITLE']} {value[1]}",    # <Название компании> <Название сделки>
                }
            ], raw=True
                                )


def update_code_1c(_deal_id):
    global logs
    deal_id = _deal_id

    # Получение информации о продукте сделки

    deal_product = requests.get(url=webhook + 'crm.deal.productrows.get.json?id=' + deal_id)

    # ID продукта сделки
    try:
        id_deal_product = str(deal_product.json()['result'][0]['PRODUCT_ID'])
    except:
        log = f'ERROR: DEAL: {deal_id} | {asctime()}'
        if log not in logs:
            logs.append(log)

    # Получение полей продукта

    product_fields = requests.get(url=webhook + 'crm.product.get.json?id=' + id_deal_product)

    # Получение кода 1С

    if product_fields.json()['result']['PROPERTY_139'] is None:
        log = f'NO CODE: DEAL: {deal_id} | {asctime()}'
        if log not in logs:
            logs.append(log)
        return "NO CODE"
    code_1c = product_fields.json()['result']['PROPERTY_139']['value']

    # Сверка кода 1С продукта и кода в сделке

    deal_1c_code = requests.get(url=f"{webhook}crm.deal.get?id={deal_id}").json()['result']['UF_CRM_1655972832']
    if deal_1c_code != code_1c:

        # Запись кода в сделку

        requests.post(url=f"{webhook}crm.deal.update?id={deal_id}&fields[UF_CRM_1655972832]={code_1c}")
        log = f'UPD: DEAL: {deal_id} | OLD_CODE: {deal_1c_code} | NEW_CODE: {code_1c} | {asctime()}'
        if log not in logs:
            logs.append(log)
        return 'UPD'


# Словарь возможных функций для вызова из кастомного запроса
custom_webhooks = {'create_task_service': create_task_service}


@app.route('/', methods=['POST', 'HEAD', 'GET'])
def result():
    if request.method == 'GET':
        return reversed(logs)
    elif request.method == 'POST':
        if request.form['event'] == 'ONCRMDEALUPDATE':
            deal_id = request.form['data[FIELDS][ID]']
            update_code_1c(deal_id)
        elif 'create_task_service' in request.url:
            if 'job' in request.args:
                job = request.args['job']
                custom_webhooks[job](request.args)
                return 'OK'
        return 'OK'
    else:
        print('Неизвестный метод запроса Http')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
