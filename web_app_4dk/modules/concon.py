from fast_bitrix24 import Bitrix
import json

import requests
from fast_bitrix24 import Bitrix
import dateutil.parser
from datetime import timedelta
from requests.auth import HTTPBasicAuth  # or HTTPDigestAuth, or OAuth1, etc.
from requests import Session
from zeep import Client
from zeep.transports import Transport

b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')

# Клиент для XML запроса
session = Session()
session.auth = HTTPBasicAuth('bitrix', 'SekXd4')
client = Client('https://cus.buhphone.com/cus/ws/PartnerWebAPI2?wsdl',
                transport=Transport(session=session))
# Получение списка сотрудников компании-клиента
company_users = client.service.ClientUserRead('Params')

# Получение списка компаний-клиентов
companies = client.service.ClientRead('Params')
print(companies)
exit()

for company in companies:
    company_inn = 1
