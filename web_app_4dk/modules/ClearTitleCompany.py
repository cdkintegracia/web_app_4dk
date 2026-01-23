from datetime import datetime
import base64
from fast_bitrix24 import Bitrix
from web_app_4dk.modules.authentication import authentication

b = Bitrix(authentication('Bitrix'))

def clear_title_company(req):

    '''
    if datetime.now().day != 1:
            #users_id = ['1391', '1']
            users_id = ['1391']
            for user_id in users_id:
                b.call('im.notify.system.add', {
                    'USER_ID': user_id,
                    'MESSAGE': f'Процесс на очистку названий компаний от доп. инфо был прерван, т.к. сегодня не первое число.'
                    })
            return False
    '''

    companies = b.get_all('crm.company.list', { 
        'filter': {'!UF_CRM_1769005130': False}, # Доп инфо в названии
        'select': ['ID', 
                   'TITLE', 
                   'UF_CRM_1769005130', # Доп инфо в названии
                   'UF_CRM_1769070499', # Доп инфо в названии (служ)
                   'UF_CRM_1769005163' # Чистое название (служ)
                   ]
        })
    
    print(len(companies))

    for company in companies:
        if company['UF_CRM_1769005163'] != False:
            '''b.call('crm.company.update',
                {'id': company['ID'],
                'fields': {
                    'UF_CRM_1769005130': '', # Доп инфо в названии
                    'UF_CRM_1769070499': '', # Доп инфо в названии (служ)
                    'TITLE': company['UF_CRM_1769005163'] # Чистое название (служ)
                }}
            )
            '''
            print('очищена компания', {company['ID']})

        else:
            #users_id = ['1391', '1']
            users_id = ['1391']
            for user_id in users_id:
                b.call('im.notify.system.add', {
                    'USER_ID': user_id,
                    'MESSAGE': f'В компании https://vc4dk.bitrix24.ru/crm/company/details/{company["ID"]}/ не заполнено "чистое" название.'
                    })

        
if __name__ == '__main__':
    clear_title_company()