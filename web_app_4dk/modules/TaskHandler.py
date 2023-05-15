from datetime import datetime, timedelta

from web_app_4dk.tools import send_bitrix_request


def check_similar_tasks_this_hour(task_info, company_id):
    users_id = [task_info['createdBy'], '311']
    if task_info['groupId'] not in ['1', '7']:
        return
    end_time_filter = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    start_time_filter = (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
    similar_tasks = send_bitrix_request('tasks.task.list', {
        'filter': {
            '>=CREATED_DATE': start_time_filter,
            '<CREATED_DATE': end_time_filter,
            'GROUP_ID': task_info['groupId'],
            'UF_CRM_TASK': ['CO_' + company_id]
        }
    })
    i = list(map(lambda x: x['id'], similar_tasks))
    print(task_info)
    for user_id in users_id:
        send_bitrix_request('im.notify.system.add', {
            'USER_ID': user_id,
            'MESSAGE': f"Текущая: {task_info['id']}\nОстальные: {i}"
        })



def fill_task_title(req):
    task_id = req['data[FIELDS_AFTER][ID]']
    task_info = send_bitrix_request('tasks.task.get', {
        'taskId': task_id,
        'select': ['*', 'UF_*']
    })

    if not task_info or 'task' not in task_info or not task_info['task']:
        return
    task_info = task_info['task']

    '''
    if task_info['closedDate'] and task_info['ufAuto934103382947'] != '1':
        send_notification(task_info, 'Завершение')
    '''

    if not task_info['ufCrmTask']:
        return

    company_crm = list(filter(lambda x: 'CO' in x, task_info['ufCrmTask']))
    uf_crm_task = []
    if not company_crm:
        contact_crm = list(filter(lambda x: 'C_' in x, task_info['ufCrmTask']))
        if not contact_crm:
            return
        contact_crm = contact_crm[0][2:]
        contact_companies = list(map(lambda x: x['COMPANY_ID'], send_bitrix_request('crm.contact.company.items.get', {'id': contact_crm})))
        if not contact_companies:
            return
        contact_companies_info = send_bitrix_request('crm.company.list', {
            'select': ['UF_CRM_1660818061808'],     # Вес сделок
            'filter': {
                'ID': contact_companies,
            }
        })
        for i in range(len(contact_companies_info)):
            if not contact_companies_info[i]['UF_CRM_1660818061808']:
                contact_companies_info[i]['UF_CRM_1660818061808'] = 0
        best_value_company = list(sorted(contact_companies_info, key=lambda x: float(x['UF_CRM_1660818061808'])))[-1]['ID']
        uf_crm_task = ['CO_' + best_value_company, 'C_' + contact_crm]
        company_id = best_value_company
    else:
        company_id = company_crm[0][3:]
    check_similar_tasks_this_hour(task_info, company_id)
    company_info = send_bitrix_request('crm.company.get', {
        'ID': company_id,
    })
    if company_info['TITLE'] in task_info['title']:
        return

    if not uf_crm_task:
        send_bitrix_request('tasks.task.update', {
            'taskId': task_id,
            'fields': {
                'TITLE': f"{task_info['title']} {company_info['TITLE']}",
            }})
    else:
        send_bitrix_request('tasks.task.update', {
            'taskId': task_id,
            'fields': {
                'TITLE': f"{task_info['title']} {company_info['TITLE']}",
                'UF_CRM_TASK': uf_crm_task,
            }})
    return task_info


def send_notification(task_info, notification_type):
    users_notification_list = ['339', '311']
    if not task_info or not task_info['auditors']:
        return
    auditors = task_info['auditors']
    task_id = task_info['id']
    flag = False
    for user in users_notification_list:
        if user in auditors:
            if notification_type == 'Создание':
                send_bitrix_request('im.notify.system.add', {'USER_ID': user,
                                                             'MESSAGE': f"Была создана новая задача, в которой вы являетесь наблюдателем:\nhttps://vc4dk.bitrix24.ru/company/personal/user/{user}/tasks/task/view/{task_id}/"})
                send_bitrix_request('im.notify.system.add', {'USER_ID': '311',
                                                             'MESSAGE': f"Была создана новая задача, в которой вы являетесь наблюдателем:\nhttps://vc4dk.bitrix24.ru/company/personal/user/{user}/tasks/task/view/{task_id}/"})
            elif notification_type == 'Завершение':
                send_bitrix_request('im.notify.system.add', {'USER_ID': user,
                                                             'MESSAGE': f"Завершена задача, в которой вы являетесь наблюдателем:\nhttps://vc4dk.bitrix24.ru/company/personal/user/{user}/tasks/task/view/{task_id}/"})
                send_bitrix_request('im.notify.system.add', {'USER_ID': '311',
                                                             'MESSAGE': f"Завершена задача, в которой вы являетесь наблюдателем:\nhttps://vc4dk.bitrix24.ru/company/personal/user/{user}/tasks/task/view/{task_id}/"})
                if not flag:
                    send_bitrix_request('tasks.task.update', {'taskId': task_info['id'], 'fields': {'UF_AUTO_934103382947': '1'}})
                    flag = True


def task_handler(req):
    task_info = fill_task_title(req)
    '''
    send_notification(task_info, 'Создание')
    '''
