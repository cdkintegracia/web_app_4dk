from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication

b = Bitrix(authentication('Bitrix'))


def complete_call_activity(req):
    activity_id = req['data[FIELDS][ID]']
    activity_info = b.get_all('crm.activity.list', {
        'filter': {
            'PROVIDER_TYPE_ID': 'CALL',
            'COMPLETED': 'N',
            'ID': activity_id
        }})
    if activity_info:
        b.get_all('crm.activity.update', {'id': activity_id, 'fields': {'COMPLETED': 'Y'}})
