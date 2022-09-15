from calendar import monthrange

from fast_bitrix24 import Bitrix

from web_app_4dk.authentication import authentication

# Считывание файла authentication.txt

webhook = authentication('Bitrix')
b = Bitrix(webhook)



def get_deals_for_task_service(date_start, date_end, type_deals, employees):
    """
    Функция, которая вызывается из функции create_task_service

    :param date_start: Дата начала фильтрации сделок
    :param date_end: Дата конца фильтрации сделок
    :param type_deals: Типы сделок для фильтрации
    :param employees: Сотрудники и отделы для фильтрации сделок
    :return: Массив найденных сделок по фильтру (состоит из 3 массивов)
    :return:
    """

    if employees == '':     # Если не были выбраны сотрудники в параметрах БП

        # Начались в сентябре 2022 и заканчиваются после сентября 2022

        deals_start_in_end_after = b.get_all(
            'crm.deal.list', {
                'filter': {
                    '>BEGINDATE': date_start,
                    '<BEGINDATE': date_end,
                    '>CLOSEDATE': date_end,
                    'UF_CRM_1662365565770': '1',    # Помощник
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
                    'UF_CRM_1662365565770': '1',    # Помощник
                }
            }
        )

        # начались до сентября 2022 и заканчиваются после сентября 2022

        deals_start_before_end_after = b.get_all(
            'crm.deal.list', {
                'filter': {
                    '<BEGINDATE': date_start,
                    '>CLOSEDATE': date_end,
                    'UF_CRM_1662365565770': '1',    # Помощник
                }
            }
        )
    else:   # Если были выбраны сотрудники в параметрах БП
        id_list = set()
        id_employees = employees.split(', ')    # Строка с сотрудниками и отделами в список
        for id in id_employees:
            if 'user' in id:    # Если в массиве найден id сотрудника
                id_list.add(id[5:])
            elif 'group' in id:     # Если в массиве найден id отдела
                department_users = b.get_all('user.get', {'filter': {'UF_DEPARTMENT': id[8:]}})
                for user in department_users:
                    id_list.add(user['ID'])
        id_list = list(id_list)

        # Начались в сентябре 2022 и заканчиваются после сентября 2022

        deals_start_in_end_after = b.get_all(
            'crm.deal.list', {
                'filter': {
                    '>BEGINDATE': date_start,
                    '<BEGINDATE': date_end,
                    '>CLOSEDATE': date_end,
                    'UF_CRM_1662365565770': '1',    # Помощник
                    'ASSIGNED_BY_ID': id_list,
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
                    'UF_CRM_1662365565770': '1',    # Помощник
                    'ASSIGNED_BY_ID': id_list,
                }
            }
        )

        # начались до сентября 2022 и заканчиваются после сентября 2022

        deals_start_before_end_after = b.get_all(
            'crm.deal.list', {
                'filter': {
                    '<BEGINDATE': date_start,
                    '>CLOSEDATE': date_end,
                    'UF_CRM_1662365565770': '1',    # Помощник
                    'ASSIGNED_BY_ID': id_list,
                }
            }
        )

    return deals_start_in_end_after + deals_start_before_end_after + deals_start_before_end_in


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
    task_text = dct['text']
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

    type_deals = [
                    'UC_XIYCTV',  # ПРОФ Земля + Помощник
                    'UC_5T4MAW',  # ПРОФ Земля + Облако + Помощник
                    'UC_2SJOEJ',  # ПРОФ Облако+Помощник
                    'UC_81T8ZR',  # АОВ
                    'UC_SV60SP',  # АОВ + Облако
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

    # Получение массива сделок

    deals = get_deals_for_task_service(date_start, date_end, type_deals, dct['employees'])

    # Разделение ID сделок по ответственному

    for deal in deals:
        employee = deal['ASSIGNED_BY_ID']   # Ответственный
        if employee not in employees:

            # Создание ключа с ID сотрудника и значение:
            # 0: ID сделки
            # 1: Название сделки
            # 2: ID компании
            employees.setdefault(employee, [[deal['ID'], deal['TITLE'], deal['COMPANY_ID'], deal['ID']]])
        else:
            # Добавление ID сделки к значению dct
            employees[employee].append([deal['ID'], deal['TITLE'], deal['COMPANY_ID'], deal['ID']])

    # Формирование задач

    for employee in employees:
        if employee not in ['None', None]:

            employee_fields = b.get_all('user.get', {"ID": employee})
            employee_name = employee_fields[0]['NAME'] + ' ' + employee_fields[0]['LAST_NAME']

            task = b.call('tasks.task.add', {
                'fields': {
                    'TITLE': f"Сервисный выезд {employee_name} {dct['month']} {str(year)}",
                    'DEADLINE': f"{str(year)}-{month}-{current_month_days} 19:00:00",
                    'RESPONSIBLE_ID': employee,
                    'ALLOW_CHANGE_DEADLINE': 'N',
                    'GROUP_ID': '71',
                    'DESCRIPTION': task_text,
                    'CREATED_BY': '173',
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

            # Создание пунктов чек-листа для созданной задачи на сотрудника

            company = b.get_all('crm.company.list', {
                'filter': {
                    'ID': value[2]
                }
            })

            b.call('task.checklistitem.add', [
                task['task']['id'], {
                    # <Название компании> <Название сделки> <Ссылка на сделку>
                    'TITLE': f"{company[0]['TITLE']} {value[1]} https://vc4dk.bitrix24.ru/crm/deal/details/{value[0]}/",
                }
            ], raw=True
                                )

            # Создание подзадачи для основной задачи

            b.call('tasks.task.add', {
                'fields': {
                    'TITLE': f"СВ: {company[0]['TITLE']} {dct['month']} {str(year)}",
                    'DEADLINE': f"{str(year)}-{month}-{current_month_days} 19:00:00",
                    'RESPONSIBLE_ID': employee,
                    'ALLOW_CHANGE_DEADLINE': 'N',
                    'GROUP_ID': '71',
                    'DESCRIPTION': f"{task_text}\n",
                    'PARENT_ID': task['task']['id'],
                    'UF_CRM_TASK': [f"CO_{company[0]['ID']}", f"D_{value[3]}"],
                    'CREATED_BY': '173',
                }
            }
                          )


        # Защита от дублирования задач

        updated_task = b.get_all('tasks.task.get', {'taskId': task['task']['id']})
        if len(updated_task['task']['checklist']) == 0:
            b.call('tasks.task.delete', {'taskId': task['task']['id']})
            print('Удалена пустая задача')

    b.call('im.notify.system.add', {'USER_ID': dct['user_id'][5:], 'MESSAGE': f'Задачи на сервисный выезд поставлены'})