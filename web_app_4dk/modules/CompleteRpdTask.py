from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication

# Считывание файла authentication.txt

webhook = authentication('Bitrix')
b = Bitrix(webhook)


def complete_rpd_task(req):
    task = b.get_all('tasks.task.get', {'taskId': req['id'], 'select': ['UF_CRM_TASK']})
    company_id = task['task']['ufCrmTask'][0].split('_')[1]
    b.call('crm.company.update', {'ID': company_id, 'fields': {'UF_CRM_1665655830': '1195'}})
