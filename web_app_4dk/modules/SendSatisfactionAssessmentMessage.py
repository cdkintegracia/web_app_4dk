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
    contact_info = b.get_all('crm.contact.get', {'ID': contact_id, 'select': ['PHONE']})
    contact_phones = list(map(lambda x: x['VALUE'], contact_info['PHONE']))
    calls = b.get_all('voximplant.statistic.get', {
        'filter': {
            'CRM_ENTITY_TYPE': 'CONTACT',
            'PHONE_NUMBER': contact_phones,
            '>CALL_START_DATE': task_info['createdDate'],
            'CALL_FAILED_CODE': '200',
            'PORTAL_USER_ID': task_info['responsibleId'],
            'CALL_TYPE': '1',

        }})

    if not calls:
        return
    call_phone_number = calls[0]['PHONE_NUMBER']
    if call_phone_number[2:5] in ['812', '812']:
        return

    b.call('crm.item.add', {
        'entityTypeId': '160',
        'fields': {
            'ufCrm39_1687268735735': call_phone_number,
            'ufCrm39_1687176023': req['task_id'],
            'title': req['task_id'],
            'assigned_by_id': '173',
            'created_by': '173',
        }
    })

    b.call('tasks.task.update', {
        'taskId': req['task_id'],
        'fields': {
            'UF_AUTO_475539459870': 'Да',
        }
    })

    b.call('bizproc.workflow.start', {
        'TEMPLATE_ID': '1561',
        'DOCUMENT_ID': ['crm', 'CCrmDocumentContact', 'CONTACT_' + contact_id],
        'PARAMETERS': {
            'commentary_text': f"По задаче https://vc4dk.bitrix24.ru/workgroups/group/1/tasks/task/view/{task_info['id']}/ клиенту было отправлено сообщение об оценке обслуживания на номер {call_phone_number}",
                    }
    })
