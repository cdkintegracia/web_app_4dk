from fast_bitrix24 import Bitrix
import openpyxl

b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')


deals = b.get_all('crm.deal.list', {'select': ['*', 'UF_*'], 'filter': {'!UF_CRM_1640523562691': None, 'UF_CRM_1670409896': None}})
for deal in deals:
    b.call('crm.deal.update', {'id': deal['id'], 'fields': {'UF_CRM_1670409896': deal['UF_CRM_1640523562691']}})