from fast_bitrix24 import Bitrix
import requests

b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')
contact_id = '11293'
companies = b.get_all('crm.contact.company.items.get', {'ID': contact_id})
companies = requests.get(url=f'https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/crm.contact.company.items.get?ID={contact_id}').json()['result']

print(companies)
