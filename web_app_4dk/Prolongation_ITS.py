from time import strftime
from calendar import monthrange

from fast_bitrix24 import Bitrix

from web_app_4dk.authentication import authentication

# Считывание файла authentication.txt

b = Bitrix(authentication('Bitrix'))

def prolongation_its(req):
    users = b.get_all('user.get', {'filter': {'UF_DEPARTMENT': '225'}})
    users_id = list(map(lambda x: x['ID'], users))
    month = strftime('%m')
    year = strftime('%Y')
    date_filter_start = f"{year}-{month}-01"
    date_filter_end = f"{year}-{month}-{monthrange(int(year), int(month))[1]}"
    deals = b.get_all('crm.deal.list', {'filter': {'ASSIGNED_BY_ID': users_id, '<=CLOSEDATE': date_filter_end, '>=CLOSEDATE': date_filter_start}})
    for deal in deals:
        company_name = b.get_all('crm.company.list', {'filter': {'ID': deal['COMPANY_ID']}})[0]['TITLE']
        b.call('tasks.task.add', {
            'fields':{
                'TITLE': f'Продление сделки {company_name}',
                'GROUP_ID': '13',
                'CREATED_BY': '173',
                'RESPONSIBLE_ID': '311',
                'DEADLINE': date_filter_end,
                'UF_CRM_TASK': ['D_' + deal['ID'], 'CO_' + deal['COMPANY_ID']],
            }
        }
               )

if __name__ == '__main__':
    prolongation_its()