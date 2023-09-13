from datetime import datetime, timedelta
from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))

deal = b.get_all('crm.deal.get', {'ID': '116857', 'select': ['*', 'UF_*']})
a = (datetime.fromisoformat(deal['UF_CRM_1638958630625']) + timedelta(days=1)).strftime('%d.%m.%Y')
print(a)