import requests

from web_app_4dk.modules.authentication import authentication


def complete_call_activity(req):
<<<<<<< Updated upstream
=======
    time_change = datetime.datetime.now()
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
=======
    else:
        activity_info_2 = requests.post(url=f"{authentication('Bitrix')}crm.activity.list", json=req_data_2).json()['result']
        if activity_info_2:
            id_element = activity_info_2[0]['OWNER_ID'] #id элемента смарт-процесса
            req_data = {'entityTypeId': 150, 'id': id_element, 'fields': {'ufCrm49ServiceField': time_change}}
            requests.post(url=f"{authentication('Bitrix')}crm.item.update", json=req_data_2)
>>>>>>> Stashed changes
