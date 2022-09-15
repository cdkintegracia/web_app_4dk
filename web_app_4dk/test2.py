import requests
from requests.auth import HTTPBasicAuth  # or HTTPDigestAuth, or OAuth1, etc.
from requests import Session
from zeep import Client
from zeep.transports import Transport
from fast_bitrix24 import Bitrix
from datetime import datetime
from datetime import timedelta
from time import time

b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')

session = Session()
session.auth = HTTPBasicAuth('bitrix', 'SekXd4')
client = Client('https://cus.buhphone.com/cus/ws/PartnerWebAPI2?wsdl',
            transport=Transport(session=session))


'''
headers = {
    'accept': 'application/json',
    # Already added when you pass json= but not when you pass data=
    # 'Content-Type': 'application/json',
}

json_data = {
    'type': 'line',
    'url': 'http://141.8.195.67:5000/1c-connect',
}

response = requests.post('https://push.1c-connect.com/v1/hook/', headers=headers, json=json_data, auth=('bitrix', 'SekXd4'))


print(response)
'''
crm_dct = {
        '1': ['Лид:', 'lead', 'L'],
        '2': ['Сделка:', 'deal', 'D'],
        '3': ['Контакт:', 'contact', 'C'],
        '4': ['Компания', 'company', 'CO']
    }
current_date = datetime.utcnow().strftime('%Y %m %d')
current_date = datetime.strptime(current_date, '%Y %m %d')
date_filter = current_date - timedelta(days=1)
date_filter = date_filter.strftime('%Y-%m-%d')
mails = b.get_all('crm.activity.list', {'filter': {'PROVIDER_TYPE_ID': 'EMAIL', '>=CREATED': date_filter}})

for mail in mails:
    print(mail)


