from fast_bitrix24 import Bitrix
import requests

b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')

contact = b.get_all('crm.contact.get', {'ID': '11293'})
photo_id = contact['PHOTO']['id']
b.call('crm.contact.update', {'ID': '11293', 'fields': {'PHOTO': {'id': photo_id, 'remove': 'Y'}}})