from fast_bitrix24 import Bitrix

try:
    from authentication import authentication
except ModuleNotFoundError:
    from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def fill_task_title(req):
    task_id = req['data[FIELDS_AFTER][ID]']
    task_info = b.get_all('tasks.task.get', {'taskId': task_id})
    print(task_info)







































