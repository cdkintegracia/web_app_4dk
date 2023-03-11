from fast_bitrix24 import Bitrix

try:
    from authentication import authentication
except ModuleNotFoundError:
    from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def fill_task_title(req):
    task_id = req['data[FIELDS_AFTER][ID]']
    task_info = b.get_all('tasks.task.get', {
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
    company_info = b.get_all('crm.company.get', {
        'ID': company_id,
    })
    if company_info['TITLE'] in task_info['title']:
        return

    b.call('tasks.task.update', {
        'taskId': task_id,
        'fields': {
            'TITLE': f"{task_info['title']} {company_info['TITLE']}"
        }})






































