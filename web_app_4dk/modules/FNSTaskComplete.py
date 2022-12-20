from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication

b = Bitrix(authentication('Bitrix'))


def fns_task_complete(req):
    uf_crm_task = 'CO_' + req['company_id']
    task = b.get_all('tasks.task.list', {'filter': {'UF_CRM_TASK': uf_crm_task, 'GROUP_ID': '89'}})

    if task:
        task = task[0]
        update_task = b.call('tasks.task.update', {'taskId': task['id'], 'fields': {'STAGE_ID': '1279', 'STATUS': '5'}})
        b.call('task.commentitem.add', [task['id'], {'POST_MESSAGE': 'Администратор изменил вендора ЭЦП в сделке. Задача была автоматически завершена', 'AUTHOR_ID': '173'}],
               raw=True)

    else:
        all_tasks = b.get_all('tasks.task.list', {'filter': {'GROUP_ID': '89'}})
        for gk_task in all_tasks:
                if req['regnumber'] in gk_task['description']:
                    all_checklists = b.get_all('task.checklistitem.getlist', {'taskId': gk_task['id']})
                    checklist = list(filter(lambda x: req['company_name'] in x['TITLE'], all_checklists))
                    if checklist:
                        checklist = checklist[0]
                        b.call('task.checklistitem.update', [gk_task['id'], checklist['ID'], {'IS_COMPLETE': 'Y'}], raw=True)
                        b.call('task.commentitem.add', [gk_task['id'], {
                            'POST_MESSAGE': f'Администратор изменил вендора ЭЦП в сделке по компании {req["company_name"]}. Соответствующий элемент чеклиста был автоматически закрыт',
                            'AUTHOR_ID': '173'}],
                               raw=True)
                        return