import base64

from fast_bitrix24 import Bitrix

from web_app_4dk.authentication import authentication

b = Bitrix(authentication('Bitrix'))


def update_contact_photo(req: dict):
    contact_id = req['data[FIELDS][ID]']
    contact_photo = b.get_all('crm.contact.list', {'selecr': ['PHOTO'], 'filter': {'ID': contact_id}})[0]
    companies = b.get_all('crm.contact.company.items.get', {'ID': contact_id})
    if companies and 'PHOTO' in contact_photo:
        b.call('crm.contact.update', {'ID': contact_id, 'fields': {'PHOTO': None}})
    elif not companies and 'PHOTO' not in contact_photo:
        with open('/root/web_app_4dk/web_app_4dk/red_square.png', 'rb') as file:
            photo = file.read()
        new_photo = base64.b64encode(photo)
        b.call('crm.contact.update', {'ID': contact_id, 'fields': {'PHOTO': {'fileData': ['red_square.png', str(new_photo)[2:]]}}})
    else:
        return
