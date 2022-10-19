from fast_bitrix24 import Bitrix


b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')

sub_deals = b.get_all('crm.deal.list', {'select': [''], 'filter': {'TYPE_ID': 'UC_OV4T7K'}})
for sub_deal in sub_deals:
