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
    elements = b.get_all('crm.item.list', {
        'entityTypeId': '161',
        'filter': {
            'companyId': [None, 'None', '']
        }
    })

    for element in elements:
        #print(element)
        company_info = send_bitrix_request('crm.company.list', {
            'select': ['*', 'UF_*'],
            'filter': {
                'UF_CRM_1656070716': element['ufCrm41_1689103279']
            }
        })
        update_fields = dict()
        if company_info:
            update_fields['companyId'] = company_info[0]['ID']
            update_fields['ufCrm41_1689862848017'] = documents_delivery[company_info[0]['UF_CRM_1638093692254']]
            update_fields['observers'] = company_info[0]['ASSIGNED_BY_ID']
        if element['ufCrm41_1690283806']:
            user_b24 = send_bitrix_request('user.get', {
                'filter': {
                    'UF_USR_1690373869887': element['ufCrm41_1690283806']
                }
            })
            if user_b24:
                update_fields['assignedById'] = user_b24[0]['ID']
            else:
                update_fields['assignedById'] = '91'
        else:
            update_fields['assignedById'] = '91'
        if element['stageId'] == 'DT161_53:NEW' and element['ufCrm41_1689101216']:
            update_fields['stageId'] = 'DT161_53:SUCCESS'
        send_bitrix_request('crm.item.update', {
            'entityTypeId': '161',
            'id': element['id'],
            'fields': update_fields
        })

    elements = b.get_all('crm.item.list', {
        'entityTypeId': '161',
        'filter': {
            'stageId': 'DT161_53:NEW',
            '!ufCrm41_1689101216': None,
        }
    })

    for element in elements:
        send_bitrix_request('crm.item.update', {
            'entityTypeId': '161',
            'id': element['id'],
            'fields': {
                'stageId': 'DT161_53:SUCCESS'
            }
        })

    send_bitrix_request('im.notify.system.add', {
        'USER_ID': req['user_id'][5:],
        'MESSAGE': f'"Элементы РТиУ заполнены'})


if __name__ == '__main__':
    fill_act_document_smart_process({'user_id': 'user_311'})