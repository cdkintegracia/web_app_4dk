from fast_bitrix24 import Bitrix

from authentication import authentication
from copy import deepcopy

b = Bitrix(authentication('Bitrix'))


def clear_phones(contact_id, phones):
    cleared_phones = deepcopy(phones)
    for i in cleared_phones:
        i['VALUE'] = ''
        b.call('crm.contact.update', {
            'ID': contact_id,
            'fields': {
                'PHONE': cleared_phones
            }
        })


def clear_contact_phone_numbers(contact_id):
    contacts = b.get_all('crm.contact.list', {
        'select': ['PHONE'],
        'filter': {
            'ID': contact_id
        }
    })

    for contact in contacts:
        flag = False
        new_phones = []
        check_phones = []
        phones = contact['PHONE']

        for phone in phones:
            if phone['VALUE'] in check_phones:
                flag = True
                break
            else:
                check_phones.append(phone['VALUE'])

        if not flag:
            return

        for phone in phones:
            phone['VALUE_TYPE'] = 'WORK'

        for i in phones:
            if i['VALUE'] not in check_phones:
                check_phones.append(i['VALUE'])
                new_phones.append(i)

        clear_phones(contact_id, phones)
        b.call('crm.contact.update', {
            'ID': contact['ID'],
            'fields': {
                'PHONE': new_phones
            }
        })
