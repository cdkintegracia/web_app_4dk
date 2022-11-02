import logging

import json

import requests
from fast_bitrix24 import Bitrix
import dateutil.parser
from datetime import timedelta
from requests.auth import HTTPBasicAuth  # or HTTPDigestAuth, or OAuth1, etc.
from requests import Session
from zeep import Client
from zeep.transports import Transport


# Клиент для XML запроса
session = Session()
session.auth = HTTPBasicAuth('bitrix', 'SekXd4')
client = Client('https://cus.buhphone.com/cus/ws/PartnerWebAPI2?wsdl',
                transport=Transport(session=session))


lines = client.service.ServiceLineKindRead('Params')[1]['Value']['row']

for line in lines:
    print(line['Value'][0], line['Value'][2])