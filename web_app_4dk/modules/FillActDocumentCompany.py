from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def fill_act_document_company(req):
    company_info = b.get_all('crm.company.list', {
        'filter': {
            'UF_CRM_1656070716': req['inn']
        }
    })

    if company_info:
        b.call('crm.item.update', {
            'entityTypeId': '161',
            'id': req['element_id'],
            'fields': {
                'companyId': company_info[0]['ID']
            }
        })