from time import time

from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def create_feedback_list_element(task_id, rating, message_type):
    message_types = {
        'WhatsApp': '2731',
        'E-mail': '2733',
        '1С:Коннект': '2735',
    }
    b.call('lists.element.add', {
        'IBLOCK_TYPE_ID': 'lists',
        'IBLOCK_ID': '273',
        'ELEMENT_CODE': time(),
        'fields': {
            'NAME': task_id,
            'PROPERTY_1729': rating,
            'PROPERTY_1739': message_types[message_type]
        }
    })


def update_feedback_list_element(task_id, rating, commentary):
    element = b.call('lists.element.get', {
        'IBLOCK_TYPE_ID': 'lists',
        'IBLOCK_ID': '273',
        'filter': {
            'NAME': task_id
        }
    })
    if isinstance(element, list):
        element = element[0]
    if not element:
        return
    b.call('lists.element.get', {
        'IBLOCK_TYPE_ID': 'lists',
        'IBLOCK_ID': '273',
        'ELEMENT_ID': element['ID'],
        'fields': {
            'PROPERTY_1729': rating,
            'PROPERTY_1741': commentary
        }
    })


def fill_feedback_task_fields(req):
    try:
        task_id = req['form_url'].split('task_id=')[1]
        task_update = b.call('tasks.task.update', {
            'taskId': task_id,
            'fields': {
                'UF_AUTO_177856763915': req['rating'],
                'UF_AUTO_917673898341': req['commentary']
            }
        })

        update_feedback_list_element(task_id, req['rating'], req['commentary'])

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
    except:
        return
