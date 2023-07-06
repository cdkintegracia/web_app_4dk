from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def complete_document_flow_task(req):
    company_name = req['company_name']
    task_name_search = f"Как будем обмениваться документами с {company_name.strip()}"
    tasks = b.get_all('tasks.task.list', {'filter': {'TITLE': task_name_search, '!STATUS': '5'}})
    if tasks:
        for task in tasks:
            b.call('tasks.task.update', {'taskId': task['id'], 'fields': {'STATUS': '5'}})
            b.call('task.commentitem.add', [task['id'], {'POST_MESSAGE': 'Способ обмена заполнен в карточке компании', 'AUTHOR_ID': '173'}], raw=True)


complete_document_flow_task({'company_name': 'ПЛАНЕТА ЗДОРОВОЙ КОЖИ 4706061700'})