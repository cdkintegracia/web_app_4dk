from web_app_4dk.tools import send_bitrix_request


def fill_task_title(req):
    task_id = req['data[FIELDS_AFTER][ID]']
    task_info = send_bitrix_request('tasks.task.get', {
        'taskId': task_id,
        'select': ['TITLE', 'UF_CRM_TASK']
    })
    if not task_info or not task_info['task']['ufCrmTask']:
        return

    task_info = task_info['task']
    company_crm = list(filter(lambda x: 'CO' in x, task_info['ufCrmTask']))
    if not company_crm:
        return

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






































