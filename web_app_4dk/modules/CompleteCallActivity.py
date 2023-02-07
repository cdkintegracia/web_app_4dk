import requests

from web_app_4dk.modules.authentication import authentication


def complete_call_activity(req):
    activity_id = req['data[FIELDS][ID]']
    req_data = {
        'filter': {
            'PROVIDER_TYPE_ID': 'CALL',
            'COMPLETED': 'N',
            'ID': activity_id
        }}
    activity_info = requests.post(url=f"{authentication('Bitrix')}crm.activity.list", data=req_data).json()['result']
    print(activity_info)
    '''
    if activity_info:
        b.get_all('crm.activity.update', {'id': activity_id, 'fields': {'COMPLETED': 'Y'}})
    '''
