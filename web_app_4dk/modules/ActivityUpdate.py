import requests
import datetime

from web_app_4dk.modules.authentication import authentication

def activity_update(req):
    print (req)
    time = datetime.datetime.now()
    time_change = time.strftime('%Y-%m-%d %H:%M')
    activity_id = req['data[FIELDS][ID]']
    req_data = {
        'filter': {
            'OWNER_TYPE_ID': '150', #id смарт-процесса
            'ID': activity_id #id дела
        }}
    activity_info = requests.post(url=f"{authentication('Bitrix')}crm.activity.list", json=req_data).json()['result']
    if activity_info:
      id_element = activity_info[0]['OWNER_ID'] #id элемента смарт-процесса
      req_data2 = {'entityTypeId': 150, 'id': id_element, 'fields': {'ufCrm49_ServiceField': time_change}}
      requests.post(url=f"{authentication('Bitrix')}crm.item.update", json=req_data2)
