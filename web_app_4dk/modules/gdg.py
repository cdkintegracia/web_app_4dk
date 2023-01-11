from fast_bitrix24 import Bitrix

b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/78nouvwz9drsony0/')

deal = b.get_all('crm.deal.list', {'select': ['UF_CRM_1657878818384'], 'filter': {'ID': '87701'}})
print(deal[0]['UF_CRM_1657878818384'])