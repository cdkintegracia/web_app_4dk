import requests
import datetime

from web_app_4dk.modules.authentication import authentication

def complete_call_activity(req):
    #time_change = datetime.datetime.now()
    time = datetime.datetime.now()
    time_change = time.strftime("%d.%m.%Y %H:%M")
    activity_id = req['data[FIELDS][ID]']
    req_data = {
        'filter': {
            'PROVIDER_TYPE_ID': 'CALL',
            'COMPLETED': 'N',
            'ID': activity_id
        }}
    req_data_2 = {
        'filter': {
            'OWNER_TYPE_ID': '150', #id смарт-процесса
            'ID': activity_id #id дела
        }}
    activity_info = requests.post(url=f"{authentication('Bitrix')}crm.activity.list", json=req_data).json()['result']
    if activity_info:
        req_data = {'id': activity_id, 'fields': {'COMPLETED': 'Y'}}
        requests.post(url=f"{authentication('Bitrix')}crm.activity.update", json=req_data)
    else:
        activity_info_2 = requests.post(url=f"{authentication('Bitrix')}crm.activity.list", json=req_data_2).json()['result']
        print('1')
        if activity_info_2:
            print('2')
            id_element = activity_info_2[0]['OWNER_ID'] #id элемента смарт-процесса
            print(id_element)
            req_data = {'entityTypeId': 150, 'id': id_element, 'fields': {'ufCrm49ServiceField': time_change}}
            print(req_data)
            requests.post(url=f"{authentication('Bitrix')}crm.item.update", json=req_data_2)
