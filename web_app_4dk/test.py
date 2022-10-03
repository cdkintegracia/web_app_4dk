from fast_bitrix24 import Bitrix

b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')

deal = b.get_all('crm.deal.list', {'filter': {'ID': '80243'}})

print(deal)