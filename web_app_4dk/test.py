from fast_bitrix24 import Bitrix
import requests

b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')

contact_photo = b.get_all('crm.contact.list', {'select': ['PHOTO'], 'filter': {'ID': '11293'}})[0]

print(contact_photo)
