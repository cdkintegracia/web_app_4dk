from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication
from web_app_4dk.tools import send_bitrix_request


b = Bitrix(authentication('Bitrix'))

documents_delivery = {
        '69': '1581',
        '71': '1583',
        '': '',
        None: '',
    }


def fill_act_document_smart_process(req):
    company_info = send_bitrix_request('crm.company.list', {
        'select': ['*', 'UF_*'],
        'filter': {
            'UF_CRM_1656070716': req['inn']
        }
    })
    update_fields = dict()
    if company_info:
        update_fields['companyId'] = company_info[0]['ID']
        update_fields['ufCrm41_1689862848017'] = documents_delivery[company_info[0]['UF_CRM_1638093692254']]
        update_fields['observers'] = company_info[0]['ASSIGNED_BY_ID']
    if req['guid']:
        user_b24 = send_bitrix_request('user.get', {
            'filter': {
                'UF_USR_1690373869887': req['guid']
            }
        })
        if user_b24:
            update_fields['assignedById'] = user_b24[0]['ID']
    else:
        update_fields['assignedById'] = '91'
    send_bitrix_request('crm.item.update', {
        'entityTypeId': '161',
        'id': req['element_id'],
        'fields': update_fields
    })


elements = b.get_all('crm.item.list', {
    'entityTypeId': '161',
})

'''
for index, element in enumerate(elements, 1):
    print(index, len(elements))
    fill_act_document_smart_process({'element_id': element['id'], 'inn': element['ufCrm41_1689103279'], 'guid': element['ufCrm41_1690283806']})
'''
