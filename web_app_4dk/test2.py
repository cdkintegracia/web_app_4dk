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

companies = b.get_all('crm.company.list', {'select': ['UF_CRM_1662728120980']})
count = 0
errors = []
for company in companies:
    count += 1
    try:
        b.call('bizproc.workflow.start', {'TEMPLATE_ID': '1111', 'DOCUMENT_ID': ['crm', 'CCrmDocumentCompany', 'COMPANY_' + company['ID']]})
    except:
        errors.append(company['ID'])
    print(company['ID'], count, '|', len(companies))
print(errors)


