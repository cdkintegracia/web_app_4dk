from fast_bitrix24 import Bitrix
from authentication import authentication
#from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))

documents_delivery = {
        '69': '1581',
        '71': '1583',
        '': '',
        None: '',
    }


def fill_act_document_smart_process(req):
    element_info = b.get_all('crm.item.get', {
        'entityTypeId': '161',
        'id': req['element_id'],
    })['item']
    print(element_info)
    exit()
    company_info = b.get_all('crm.company.list', {
        'select': ['*', 'UF_*'],
        'filter': {
            'UF_CRM_1656070716': element_info['ufCrm41_1689103279']
        }
    })[0]
    update_fields = {}
    update_fields['companyId'] = company_info['ID']
    update_fields['ufCrm41_1689862848017'] = documents_delivery[company_info['UF_CRM_1638093692254']]
    update_fields['assignedById'] = company_info['ASSIGNED_BY_ID']
    b.call('crm.item.update', {
        'entityTypeId': '161',
        'id': req['element_id'],
        'fields': update_fields
    })


#fill_act_document_smart_process({'element_id': '47'})
