import requests
from requests.auth import HTTPBasicAuth  # or HTTPDigestAuth, or OAuth1, etc.
from requests import Session
from zeep import Client
from zeep.transports import Transport
from fast_bitrix24 import Bitrix

b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')

session = Session()
session.auth = HTTPBasicAuth('bitrix', 'SekXd4')
client = Client('https://cus.buhphone.com/cus/ws/PartnerWebAPI2?wsdl',
            transport=Transport(session=session))

s = '<buhphone><name>2d1dd0bd-fa0f-11e4-80d2-0025904f970d</name></buhphone>'
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

list_elements = b.get_all('lists.element.get', {
            'IBLOCK_TYPE_ID': 'lists',
            'IBLOCK_ID': '175',
            'filter': {
                'ID': '135829'
            }
        }
                                  )
print(list_elements)
for element in list_elements:
    try:
        for field_value in element['PROPERTY_1315']:
            first_break_limit = element['PROPERTY_1315'][field_value]
        for field_value in element['PROPERTY_1315']:
            second_break_limit = element['PROPERTY_1317'][field_value]
    except:
        first_break_limit = '2207'
        second_break_limit = '2209'
print(first_break_limit, second_break_limit)

list_elements = b.get_all('lists.element.update', {
            'IBLOCK_TYPE_ID': 'lists',
            'IBLOCK_ID': '175',
            'ELEMENT_ID': '135829',
    'fields': {'NAME': 'test'}
        }
                                  )
