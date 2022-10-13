from datetime import datetime
from calendar import monthrange

from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication

# Считывание файла authentication.txt

webhook = authentication('Bitrix')
b = Bitrix(webhook)


def create_task_rpd(req):
    months = {
        1: 'Январь',
        2: 'Февраль',
        3: 'Март',
        4: 'Апрель',
        5: 'Май',
        6: 'Июнь',
        7: 'Июль',
        8: 'Август',
        9: 'Сентябрь',
        10: 'Октябрь',
        11: 'Ноябрь',
        12: 'Декабрь',
    }
    current_month = months[datetime.now().month]
    current_year = datetime.now().year
    current_monthrange = monthrange(current_year, datetime.now().month)

    # Получение массива сделок
    if req['employees'] == '':
        deals = b.get_all('crm.deal.list', {
            'select': ['ID', 'COMPANY_ID', 'ASSIGNED_BY_ID', 'TITLE'],
            'filter': {
                'UF_CRM_1657878818384': '859',
                'STAGE_ID': ['C1:NEW', 'C1:UC_0KJKTY', 'C1:UC_3J0IH6'],
            }})
    else:
        id_list = set()
        id_employees = req['employees'].split(', ')  # Строка с сотрудниками и отделами в список
        for id in id_employees:
            if 'user' in id:  # Если в массиве найден id сотрудника
                id_list.add(id[5:])
            elif 'group' in id:  # Если в массиве найден id отдела
                department_users = b.get_all('user.get', {'filter': {'UF_DEPARTMENT': id[8:]}})
                for user in department_users:
                    id_list.add(user['ID'])
        id_list = list(id_list)
        deals = b.get_all('crm.deal.list', {
            'select': ['ID', 'COMPANY_ID', 'ASSIGNED_BY_ID', 'TITLE'],
            'filter': {
                'UF_CRM_1657878818384': '859',
                'STAGE_ID': ['C1:NEW', 'C1:UC_0KJKTY', 'C1:UC_3J0IH6'],
                'ASSIGNED_BY_ID': id_list
            }})

    # Разделение ID сделок по ответственному
    employees = {}
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

    # Создание задач
    for employee in employees:
        if employee not in ['None', None]:
            employee_fields = b.get_all('user.get', {"ID": employee})
            employee_name = employee_fields[0]['NAME'] + ' ' + employee_fields[0]['LAST_NAME']
            is_main_task_exists = b.get_all('tasks.task.list', {
                'select': ['ID'],
                'filter': {'TITLE': f"РПД: {employee_name} {current_month} {current_year}",
                           'GROUP_ID': '79'
                           }})
            if not is_main_task_exists:
                task = b.call('tasks.task.add', {
                    'fields': {
                        'TITLE': f"РПД: {employee_name} {current_month} {current_year}",
                        'DEADLINE': f"{current_year}-{current_month}-{current_monthrange} 19:00:00",
                        'RESPONSIBLE_ID': '173',
                        'ALLOW_CHANGE_DEADLINE': 'N',
                        'GROUP_ID': '79',
                        'CREATED_BY': '173',
                    }})
                main_task = task['task']['id']
            else:
                main_task = is_main_task_exists[0]['id']

        for value in employees[employee]:
            if employee in [None, 'None']:
                continue
            company = b.get_all('crm.company.list', {'filter': {'ID': value[2]}})[0]

            # Проверка была ли создана подзадача, для возможности допостановки
            is_sub_task_exists = b.get_all('tasks.task.list', {
                'select': ['ID'],
                'filter': {'TITLE': f"РПД: {company['TITLE']} {current_month} {current_year}",
                           'GROUP_ID': '79'
                           }})
            if is_sub_task_exists:
                continue

            # Создание пунктов чек-листа для созданной задачи на сотрудника
            b.call('task.checklistitem.add', [
                main_task, {
                    # <Название компании> <Название сделки> <Ссылка на сделку>
                    'TITLE': f"{company['TITLE']} {value[1]} https://vc4dk.bitrix24.ru/crm/deal/details/{value[0]}/",
                }
            ], raw=True
                   )

            # Создание подзадачи для основной задачи
            b.call('tasks.task.add', {
                'fields': {
                    'TITLE': f"РПД: {company['TITLE']} {current_month} {current_year}",
                    'DEADLINE': f"{current_year}-{current_month}-{current_monthrange} 19:00:00",
                    #'RESPONSIBLE_ID': employee,
                    'RESPONSIBLE_ID': '173',
                    'ALLOW_CHANGE_DEADLINE': 'N',
                    'GROUP_ID': '79',
                    'DESCRIPTION': f"",
                    'PARENT_ID': main_task,
                    'UF_CRM_TASK': [f"CO_{company['ID']}", f"D_{value[3]}"],
                    'CREATED_BY': '173',
                }})

        # Защита от дублирования задач
        updated_task = b.get_all('tasks.task.get', {'taskId': main_task})
        if len(updated_task['task']['checklist']) == 0:
            b.call('tasks.task.delete', {'taskId': main_task})
            print('Удалена пустая задача')

    b.call('im.notify.system.add', {'USER_ID': req['user_id'][5:], 'MESSAGE': f'Задачи на РПД поставлены'})

