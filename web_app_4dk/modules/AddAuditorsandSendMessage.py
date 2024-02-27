from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def send_company_responsible_tlp_message(req):
    task_info = b.get_all('tasks.task.get', {
        'select': ['*', 'UF_*'],
        'taskId': req['task_id']
    })['task']
    if 'ufCrmTask' not in task_info or not task_info['ufCrmTask']:
        return

    uf_crm_task_company = list(filter(lambda x: 'CO_' in x, task_info['ufCrmTask']))
    if not uf_crm_task_company:
        return

    company_id = uf_crm_task_company[0][3:]
    company_info = b.get_all('crm.company.get', {
        'ID': company_id
    })
    b.call('im.notify.system.add', {
        'USER_ID': company_info['ASSIGNED_BY_ID'],
        'MESSAGE': f'Для вашего клиента {company_info["TITLE"]} поставлена задача https://vc4dk.bitrix24.ru/workgroups/group/1/tasks/task/view/{task_info["id"]}/'})
    audit = task_info['auditors']
    audit.append('ASSIGNED_BY_ID')
    b.call('tasks.task.update', {
        'taskId': task_id,
        'fields': {
            'AUDITORS': audit
        }})
