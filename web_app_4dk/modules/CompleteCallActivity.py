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
    activity_info = requests.post(url=f"{authentication('Bitrix')}crm.activity.list", json=req_data).json()['result']
    if activity_info:
        req_data = {'id': activity_id, 'fields': {'COMPLETED': 'Y'}}
        requests.post(url=f"{authentication('Bitrix')}crm.activity.update", json=req_data)


