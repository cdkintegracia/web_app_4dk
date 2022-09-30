import base64

from fast_bitrix24 import Bitrix

from authentication import authentication

b = Bitrix(authentication('Bitrix'))


def update_contact_photo(req: dict):
    contact_id = req['data[FIELDS][ID]']
    companies = b.get_all('crm.contact.company.items.get', {'ID': contact_id})
    if companies:
        return
    with open('/root/web_app_4dk/web_app_4dk/red_square.png', 'rb') as file:
        photo = file.read()
    new_photo = base64.b64encode(photo)
    b.call('crm.contact.update', {'ID': contact_id, 'fields': {'PHOTO': {'fileData': ['red_square.png', str(new_photo)[2:]]}}})
