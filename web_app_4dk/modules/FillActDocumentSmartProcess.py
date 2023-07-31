from time import sleep

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
    bad_counter = 0
    users = b.get_all('user.get', {
        'filter': {
            '!UF_USR_1690373869887': None
        }
    })
    elements = b.get_all('crm.item.list', {
        'entityTypeId': '161',
        'filter': {
            'companyId': [None, 'None', '']
        }
    })
    if not elements:
        send_bitrix_request('im.notify.system.add', {
            'USER_ID': '311',
            'MESSAGE': f'Было обновлено 0 элементов РТиУ'
        })
        return
    new_companies = list()
    for element in elements:
        sleep(1)
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
            update_fields['ufCrm41_1690546413'] = company_info[0]['TITLE']
        update_fields['ufCrm41_1690807843'] = int(element['ufCrm41_1689101306'].split('-')[-1])
        if element['ufCrm41_1690546413']:
            user_b24 = list(filter(lambda x: element['ufCrm41_1690283806'] == x['UF_USR_1690373869887'], users))
            if user_b24:
                update_fields['assignedById'] = user_b24[0]['ID']
            else:
                update_fields['assignedById'] = '91'
                bad_counter += 1
        else:
            update_fields['assignedById'] = '91'
            bad_counter += 1

        if update_fields['assignedById'] == '91':
            if element['ufCrm41_1690283806'] == '4f4d8faa-c928-11e6-8a6d-aa3d71163f04':
                update_fields['assignedById'] = '169'
            elif element['ufCrm41_1690283806'] == 'e0677df2-dd6e-11e6-8e7c-0050569f0c3a':
                update_fields['assignedById'] = '161'

        if element['stageId'] == 'DT161_53:NEW' and element['ufCrm41_1689101216']:
            update_fields['stageId'] = 'DT161_53:SUCCESS'
        send_bitrix_request('crm.item.update', {
            'entityTypeId': '161',
            'id': element['id'],
            'fields': update_fields
        })

        if not company_info:
            company = send_bitrix_request('crm.company.add', {
                'fields': {
                    'TITLE': element['ufCrm41_1689103279'],
                    'ASSIGNED_BY_ID': update_fields['assignedById'],
                    'UF_CRM_1656070716': element['ufCrm41_1689103279'],
                    'COMPANY_TYPE': 'CUSTOMER'
                }
            })
            new_companies.append(f"ИНН: {element['ufCrm41_1689103279']} https://vc4dk.bitrix24.ru/crm/company/details/{company}/\n")

    if new_companies:
        task = send_bitrix_request('tasks.task.add', {
            'fields': {
                'TITLE': 'Новые компании РТиУ',
                'DESCRIPTION': f'При выгрузке РТиУ для следующих компаний не найдено соответствий в Б24, поэтому компании были созданы в Б24:\n\n'
                               f'{new_companies}',
                'GROUP_ID': '13',
                'RESPONSIBLE_ID': '311',
                'CREATED_BY': '173'

            }
        })['task']['id']

        for row in new_companies:
            b.call('task.checklistitem.add', [task, {'TITLE': row}], raw=True)

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
        'MESSAGE': f'Элементы РТиУ заполнены\n'
                   f'Плохих элементов {bad_counter}'})


if __name__ == '__main__':
    fill_act_document_smart_process({'user_id': 'user_311'})