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
    if call_phone_number[2:5] == in ['812', '812']:
        return
    print(call_phone_number[2:5])


data = {
    'task_id': '104455'
}
send_satisfaction_assessment_message(data)