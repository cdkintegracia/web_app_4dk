from web_app_4dk.tools import send_bitrix_request


def fill_uf_crm_task(req):
    pass


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
    if not company_crm:
        contact_crm = list(filter(lambda x: 'C_' in x, task_info['ufCrmTask']))
        if not contact_crm:
            return
        contact_crm = contact_crm[0][2:]
        contact_companies = send_bitrix_request('crm.contact.company.items.get', {'id': contact_crm})
        print(contact_companies)

    company_id = company_crm[0][3:]
    company_info = send_bitrix_request('crm.company.get', {
        'ID': company_id,
    })
    if company_info['TITLE'] in task_info['title']:
        return

    send_bitrix_request('tasks.task.update', {
        'taskId': task_id,
        'fields': {
            'TITLE': f"{task_info['title']} {company_info['TITLE']}"
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
