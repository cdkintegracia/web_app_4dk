from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def change_task_group(req):
    groups_and_departments = {
        '9': [361, 225],
    }
    user_info = b.get_all('user.get', {'filter': {'ID': req['responsible_id'][5:]}})[0]
    for group in groups_and_departments:
        for department in groups_and_departments[group]:
            if department in user_info['UF_DEPARTMENT']:
                b.call('tasks.task.update', {'taskId': req['task_id'], 'fields': {'GROUP_ID': group}})
                return
