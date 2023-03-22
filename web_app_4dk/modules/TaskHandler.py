from web_app_4dk.tools import send_bitrix_request


def fill_task_title(req):
    task_id = req['data[FIELDS_AFTER][ID]']
    task_info = send_bitrix_request('tasks.task.get', {
        'taskId': task_id,
        'select': ['TITLE', 'UF_CRM_TASK']
    })
    if not task_info or not task_info['task']['ufCrmTask']:
        return task_info

    task_info = task_info['task']
    company_crm = list(filter(lambda x: 'CO' in x, task_info['ufCrmTask']))
    if not company_crm:
        return task_info

    company_id = company_crm[0][3:]
    company_info = send_bitrix_request('crm.company.get', {
        'ID': company_id,
    })
    if company_info['TITLE'] in task_info['title']:
        return task_info

    send_bitrix_request('tasks.task.update', {
        'taskId': task_id,
        'fields': {
            'TITLE': f"{task_info['title']} {company_info['TITLE']}"
        }})
    return task_info


def send_notification(task_info):
    if not task_info['task'] or not task_info['task']['AUDITORS']:
        return
    auditors = task_info['task']['AUDITORS']
    users_notification_list = ['311']
    send_bitrix_request('im.notify.system.add', {'USER_ID': '311', 'MESSAGE': auditors})


def task_handler(req):
    task_info = fill_task_title(req)
    send_notification(task_info)
