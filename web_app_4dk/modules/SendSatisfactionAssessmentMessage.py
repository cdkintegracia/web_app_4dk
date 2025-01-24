from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication
from web_app_4dk.modules.ClearContactPhoneNumbers import clear_contact_phone_numbers


b = Bitrix(authentication('Bitrix'))


def send_satisfaction_assessment_message(req):
    #test = b.get_all('tasks.task.get', {'taskId': req['task_id'], 'select': ['*', 'UF_*']})
    #print(test)
    task_info = b.get_all('tasks.task.get', {'taskId': req['task_id'], 'select': ['*', 'UF_*']})['task']
    #task_info = b.get_all('tasks.task.get', {'taskId': req['task_id'], 'select': ['*', 'UF_*']})
    if not task_info:
        return
    contact_id = list(filter(lambda x: 'C_' in x, task_info['ufCrmTask']))
    if not contact_id:
        return
    contact_id = contact_id[0][2:]
    contact_info = b.get_all('crm.contact.get', {'ID': contact_id, 'select': ['PHONE']})
    contact_phones = list(map(lambda x: x['VALUE'], contact_info['PHONE']))
    #calls = b.get_all('voximplant.statistic.get', {
    calls = b.call('voximplant.statistic.get', {
        'filter': {
            'CRM_ENTITY_TYPE': 'CONTACT',
            'PHONE_NUMBER': contact_phones,
            '>CALL_START_DATE': task_info['createdDate'],
            'CALL_FAILED_CODE': '200',
            'PORTAL_USER_ID': task_info['responsibleId'],
            'CALL_TYPE': '1',

        }},
        raw=True)

    if not calls:
        return
    #call_phone_number = calls[0]['PHONE_NUMBER']
    '''
    call_phone_number = calls['result'][0]['PHONE_NUMBER']
    if '812' in call_phone_number[:6]:
        return
    '''
    try:
        call_phone_number = calls['result'][0]['PHONE_NUMBER']
        if '812' in call_phone_number[:6]:
            return
    except:
        call_phone_number =''
        
    contact_emails = b.get_all('crm.contact.get', {
        'ID': contact_id,
        'select': ['EMAIL']
    })

    try:
        contact_email = contact_emails['EMAIL'][0]['VALUE']
    except:
        contact_email = ''

    b.call('crm.item.add', {
        'entityTypeId': '160',
        'fields': {
            'ufCrm39_1687268735735': call_phone_number,
            'ufCrm39_1687176023': req['task_id'],
            'ufCrm39_1687955868': contact_email,
            'title': req['task_id'],
            'assigned_by_id': '173',
            'created_by': '173',
        }
    })

    clear_contact_phone_numbers(contact_id)

    '''
    b.call('bizproc.workflow.start', {
        'TEMPLATE_ID': '1561',
        'DOCUMENT_ID': ['crm', 'CCrmDocumentContact', 'CONTACT_' + contact_id],
        'PARAMETERS': {
            'commentary_text': f"По задаче https://vc4dk.bitrix24.ru/workgroups/group/1/tasks/task/view/{task_info['id']}/ клиенту было отправлено сообщение об оценке обслуживания на номер {call_phone_number}",
                    }
    })
    '''
