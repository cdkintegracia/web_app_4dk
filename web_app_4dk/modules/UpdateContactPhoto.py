import base64

from fast_bitrix24 import Bitrix
import requests

from web_app_4dk.modules.authentication import authentication

b = Bitrix(authentication('Bitrix'))


def update_contact_photo(req: dict):
    contact_id = req['data[FIELDS][ID]']
    contact = requests.get(url=f'{authentication("Bitrix")}crm.contact.list?select[]=PHOTO&filter[ID]={contact_id}').json()['result'][0]
    companies = requests.get(url=f'{authentication("Bitrix")}crm.contact.company.items.get?ID={contact_id}').json()['result']

    if 'PHOTO' in contact:
        if companies and contact['PHOTO'] is not None:
            photo_id = contact['PHOTO']['id']
            data = {'ID': contact_id, 'fields': {'PHOTO': {'id': photo_id, 'remove': 'Y'}}}
            #b.call('crm.contact.update', {'ID': contact_id, 'fields': {'PHOTO': {'id': photo_id, 'remove': 'Y'}}})
            requests.post(url=f"{authentication('Bitrix')}crm.contact.update", json=data)
    elif not companies and ('PHOTO' not in contact or contact['PHOTO'] is None):
        with open('/root/web_app_4dk/web_app_4dk/images.png', 'rb') as file:
            photo = file.read()
        new_photo = base64.b64encode(photo)
        data = {'ID': contact_id, 'fields': {'PHOTO': {'fileData': ['red_square.png', str(new_photo)[2:]]}}}
        requests.post(url=f"{authentication('Bitrix')}crm.contact.update", json=data)
        #b.call('crm.contact.update', {'ID': contact_id, 'fields': {'PHOTO': {'fileData': ['red_square.png', str(new_photo)[2:]]}}})
    else:
        return
