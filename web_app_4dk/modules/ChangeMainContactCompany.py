from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def change_main_contact_company(req):
    companies = b.get_all('crm.contact.company.items.get', {'ID': req['contact_id']})
    companies = list(map(lambda x: x['COMPANY_ID'], companies))
    companies.insert(0, req['company_id'])
    b.call('crm.contact.update', {
        'ID': req['contact_id'],
        'fields': {
            'COMPANY_ID':  req['company_id'],
            'COMPANY_IDS': companies
        }
    })
