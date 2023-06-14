from fast_bitrix24 import Bitrix

try:
    from authentication import authentication
except ModuleNotFoundError:
    from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def send_satisfaction_assessment_message(req):
    task_info = b.get_all('tasks.task.get', {'taskId': req['task_id'], 'select': ['*', 'UF_*']})['task']
    contact_id = list(filter(lambda x: 'C_' in x, task_info['ufCrmTask']))
    if not contact_id:
        return
    contact_id = contact_id[0][2:]



data = {
    'task_id': '104455'
}
send_satisfaction_assessment_message(data)