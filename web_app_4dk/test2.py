import requests
from requests.auth import HTTPBasicAuth  # or HTTPDigestAuth, or OAuth1, etc.
from requests import Session
from zeep import Client
from zeep.transports import Transport

session = Session()
session.auth = HTTPBasicAuth('bitrix', 'SekXd4')
client = Client('https://cus.buhphone.com/cus/ws/PartnerWebAPI2?wsdl',
            transport=Transport(session=session))

a = client.service.DepartmentRead('Params')

headers = {
    'accept': 'application/json',
    # Already added when you pass json= but not when you pass data=
    # 'Content-Type': 'application/json',
}

json_data = {
    'type': 'line',
    'url': 'http://141.8.194.146:5000/',
}

response = requests.post('https://push.1c-connect.com/v1/hook/', headers=headers, json=json_data, auth=('bitrix', 'SekXd4'))

print(response)

