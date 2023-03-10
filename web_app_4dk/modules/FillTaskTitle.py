from fast_bitrix24 import Bitrix

try:
    from authentication import authentication
except ModuleNotFoundError:
    from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def fill_task_title(req):
    task_id = req['data[FIELDS_AFTER][ID]']
    task_info = b.get_all('tasks.task.get', {'taskId': task_id, 'select': ['TITLE', 'UF_CRM_TASK']})['task']
    uf_crm_task = ''
    for crm_id in task_info['ufCrmTask']:
        if 'CO' in crm_id:
            uf_crm_task = crm_id[:3]
            break
    print(task_info['ufCrmTask'])
    print(uf_crm_task)







































