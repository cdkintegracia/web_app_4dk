import builtins

from fast_bitrix24 import Bitrix

from authentication import authentication

b = Bitrix(authentication('Bitrix'))


l = b.get_all('lists.element.get', {
    'IBLOCK_TYPE_ID': 'lists',
    'IBLOCK_ID': '269',
    'ELEMENT_ID': '488007'})

print(l)