from time import time

from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def create_feedback_list_element(task_id, rating):
    b.call('lists.element.add', {
        'IBLOCK_TYPE_ID': 'lists',
        'IBLOCK_ID': '273',
        'ELEMENT_CODE': time(),
        'fields': {
            'TITLE': task_id,
            'PROPERTY_1729': rating,
        }
    })


def fill_feedback_task_fields(req):
    task_id = req['form_url'].split('task_id=')[1]
    task_update = b.call('tasks.task.update', {
        'taskId': task_id,
        'fields': {
            'UF_AUTO_177856763915': req['rating'],
            'UF_AUTO_917673898341': req['commentary']
        }
    })

    create_feedback_list_element(task_id, req['rating'])

    if int(req['rating']) < 5:
        b.call('tasks.task.add', {
            'fields': {
                'GROUP_ID': '13',
                'TITLE': 'Оценка обслуживания меньше 5',
                'DESCRIPTION': f"Задача: https://vc4dk.bitrix24.ru/workgroups/group/1/tasks/task/view/{task_id}/\n"
                               f"Оценка: {req['rating']}\n"
                               f"Комментарий: {req['commentary']}",
                'CREATED_BY': '173',
                'RESPONSIBLE_ID': '173',
            }
        })
