from fast_bitrix24 import Bitrix
from bitrix24 import *
import requests

bx24 = Bitrix24('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')

contact_id = '11283'

#print(bx24.callMethod('crm.contact.update', ID=contact_id, fields={'NAME': 'test123'}))

contact = requests.post(url=

data = {'ID': contact_id, 'fields': {'PHOTO': {'id': photo_id, 'remove': 'Y'}}})

requests.post(f"https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/crm.contact.update", json=data)





