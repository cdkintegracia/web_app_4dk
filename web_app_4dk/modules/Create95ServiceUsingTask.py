from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def create_95_service_using_task(req):
    task_title = f"Для {req['company_name']} использование сервиса {req['service_name']} достигло 95% лимита"
    tasks = b.get_all('tasks.task.list', {
        'filter': {
            'TITLE': task_title
        }
    })
    print(tasks[0])
