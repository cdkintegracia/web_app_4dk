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

    if company_info['ASSIGNED_BY_ID'] in ['129']:
        b.call('im.notify.system.add', {
            'USER_ID': company_info['ASSIGNED_BY_ID'],
            'MESSAGE': f'Для вашего клиента {company_info["TITLE"]} поставлена задача на ТЛП https://vc4dk.bitrix24.ru/workgroups/group/1/tasks/task/view/{task_info["id"]}/'})
    #предупреждение, если тип клиента = Закончился ИТС
    if company_info['COMPANY_TYPE'] in ['UC_E99TUC'] and task_info['groupId'] in ['7']:
        b.call('im.notify.system.add', {
            #'USER_ID': company_info['ASSIGNED_BY_ID'],
            'USER_ID': '1',
            'MESSAGE': f'Для клиента без ИТС {company_info["TITLE"]} поставлена задача https://vc4dk.bitrix24.ru/workgroups/group/1/tasks/task/view/{task_info["id"]}/'})
