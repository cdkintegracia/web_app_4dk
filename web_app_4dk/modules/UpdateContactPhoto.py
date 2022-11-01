import base64
from os import remove as os_remove

from fast_bitrix24 import Bitrix
import requests

from web_app_4dk.modules.authentication import authentication

b = Bitrix(authentication('Bitrix'))


def update_contact_photo(req: dict):
    contact_id = req['data[FIELDS][ID]']
    data = {
        'select': ['PHOTO'],
        'filter': {
            'ID': contact_id
        }
    }
    contact = requests.post(url=f'{authentication("Bitrix")}crm.contact.list', json=data).json()['result'][0]
    data = {
        'ID': contact_id
    }
    companies = requests.post(url=f'{authentication("Bitrix")}crm.contact.company.items.get', json=data).json()['result']

    if 'PHOTO' in contact and companies:
        if contact['PHOTO'] is not None:
            photo_id = contact['PHOTO']['id']
            data = {'ID': contact_id, 'fields': {'PHOTO': {'id': photo_id, 'remove': 'Y'}}}
            requests.post(url=f"{authentication('Bitrix')}crm.contact.update", json=data)
    else:
        if not companies:
            if 'PHOTO' not in contact or contact['PHOTO'] in [None, 'None']:
                r = requests.get(
                    'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ad/Square_Yellow.svg/1200px-Square_Yellow.svg.png')
                with open('/root/web_app_4dk/web_app_4dk/red_square.png', 'wb') as file:
                    file.write(r.content)
                with open('/root/web_app_4dk/web_app_4dk/red_square.png', 'rb') as file:
                    photo = file.read()
                new_photo = base64.b64encode(photo)
                data = {'ID': contact_id, 'fields': {'PHOTO': {'fileData': ['red_square.png', str(new_photo)[2:]]}}}
                requests.post(url=f"{authentication('Bitrix')}crm.contact.update", json=data)
                '''
                try:
                    #os_remove('/root/web_app_4dk/web_app_4dk/red_square.png')
                except:
                    pass
                '''

