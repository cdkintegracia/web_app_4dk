from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


deal = b.get_all('crm.deal.get', {
    'ID': '105291',
    'select': ['*', 'UF_*']
})
print(deal)