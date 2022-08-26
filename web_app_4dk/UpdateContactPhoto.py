from fast_bitrix24 import Bitrix

webhook = 'https://vc4dk.bitrix24.ru/rest/311/r1oftpfibric5qym/'
b = Bitrix(webhook)


upd = b.call('crm.contact.update', {'filter': {'ID': '11023'}, 'fields': {'PHOTO': 1}})