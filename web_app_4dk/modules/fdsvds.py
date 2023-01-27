from fast_bitrix24 import Bitrix

from authentication import authentication

b = Bitrix(authentication('Bitrix'))

a = b.get_all('crm.item.get', {'entityTypeId': '141', 'id': '343'})
print(a)