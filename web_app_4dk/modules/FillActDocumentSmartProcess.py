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
    element_info = send_bitrix_request('crm.item.get', {
        'entityTypeId': '161',
        'id': req['element_id'],
    })['item']
    company_info = send_bitrix_request('crm.company.list', {
        'select': ['*', 'UF_*'],
        'filter': {
            'UF_CRM_1656070716': element_info['ufCrm41_1689103279']
        }
    })[0]
    update_fields = {}
    update_fields['companyId'] = company_info['ID']
    update_fields['ufCrm41_1689862848017'] = documents_delivery[company_info['UF_CRM_1638093692254']]
    update_fields['observers'] = company_info['ASSIGNED_BY_ID']
    update_fields['assignedById'] = '173'
    if element_info['ufCrm41_1690283806']:
        users = send_bitrix_request('user.get')
        sou_fio = element_info['ufCrm41_1690283806'].split()
        user_info = list(filter(lambda x: sou_fio[0] == x['LAST_NAME'] and sou_fio[1] == x['NAME'], users))
        if user_info:
            update_fields['assignedById'] = user_info[0]['ID']
    send_bitrix_request('crm.item.update', {
        'entityTypeId': '161',
        'id': req['element_id'],
        'fields': update_fields
    })