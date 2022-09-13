import requests
from requests.auth import HTTPBasicAuth  # or HTTPDigestAuth, or OAuth1, etc.
from requests import Session
from zeep import Client
from zeep.transports import Transport

session = Session()
session.auth = HTTPBasicAuth('bitrix', 'SekXd4')
client = Client('https://cus.buhphone.com/cus/ws/PartnerWebAPI2?wsdl',
            transport=Transport(session=session))
company = client.service.ClientRead('Params')

user_companies = client.service.ClientUserRead('Params')

for i in user_companies[1]['Value']['row']:
    if i['Value'][0] == '1485315e-d77b-4fae-bbb4-618cfb90a5e7':
        company_id = i['Value'][1]
        user_name = f"{i['Value'][4]} {i['Value'][5]}"
        for j in company[1]['Value']['row']:
            if company_id == j['Value'][0]:
                inn = j['Value'][4]
                break
        break
print(user_name, inn)

'''
headers = {
    'accept': 'application/json',
    # Already added when you pass json= but not when you pass data=
    # 'Content-Type': 'application/json',
}

json_data = {
    'type': 'line',
    'url': 'http://141.8.194.146:5000/1c-connect',
}

response = requests.post('https://push.1c-connect.com/v1/hook/', headers=headers, json=json_data, auth=('bitrix', 'SekXd4'))


print(response)

'''

