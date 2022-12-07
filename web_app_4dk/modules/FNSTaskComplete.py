from fast_bitrix24 import Bitrix

b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')


def fns_task_complete(req):
    uf_crm_task = 'CO_' + req['company_id']
    task = b.get_all('tasks.task.list', {'filter': {'UF_CRM_TASK': uf_crm_task, 'GROUP_ID': '89'}})

    if task:
        task = task[0]
        update_task = b.call('tasks.task.update', {'taskId': task['id'], 'fields': {'STAGE_ID': '1279', 'STATUS': '5'}})

    else:
        all_tasks = b.get_all('tasks.task.list', {'filter': {'GROUP_ID': '89'}})
        for gk_task in all_tasks:
                if req['regnumber'] in gk_task['description']:
                    print(gk_task)
                    all_checklists = b.get_all('task.checklistitem.getlist', {'taskId': gk_task['id']})
                    checklist = list(filter(lambda x: req['company_name'] in x['TITLE'], all_checklists))
                    if checklist:
                        checklist = checklist[0]
                        b.call('task.checklistitem.update', [gk_task['id'], checklist['ID'], {'IS_COMPLETE': 'Y'}], raw=True)
                        return



req = {
    'company_id': '',
    'regnumber': '800308713',
    'company_name': 'ТЕРМОСЕНС 4705075517'
}
fns_task_complete(req)