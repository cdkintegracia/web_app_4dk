from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def create_paid_task(req):
    task_info = b.get_all('tasks.task.get', {
        'taskId': req['task_id'],
        'select': ['*', 'UF_*']
    })['task']
    try:
        uf_crm_task = task_info['ufCrmTask']
    except:
        uf_crm_task = []
    b.call('tasks.task.add', {
        'fields': {
            'TITLE': 'Платная задача завершена! Выставьте счет клиенту.',
            'DESCRIPTION': f'Завершена платная задача.\n'
                           f'Ссылка на задачу: {req["task_url"]}\n\n'
                           f'Информация о задаче:\n'
                           f'Группа: {req["group"]}\n'
                           f'Название: {req["title"]}\n'
                           f'Описание: {req["description"]}\n'
                           f'Статус: {req["status"]}\n'
                           f'Постановщик: {req["created_by"]}\n'
                           f'Ответственный: {req["responsible"]}\n'
                           f'Дата создания: {req["created_date"]}\n'
                           f'Дата закрытия: {req["close_date"]}\n'
                           f'Трудозатраты: {req["time"]}',
            'GROUP_ID': '11',
            'CREATED_BY': '173',
            'RESPONSIBLE_ID': '173',
            'UF_CRM_TASK': uf_crm_task
        }
    })