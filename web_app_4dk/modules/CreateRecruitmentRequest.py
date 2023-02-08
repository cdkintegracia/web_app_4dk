from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def create_recruitment_request(req):
    department_info = b.get_all('department.get', {'ID': req['department']})
    department_name = department_info[0]['NAME']
    print(req['responsible'][5:])
    b.call('crm.item.add', {
        'entityTypeId': '130',
        'fields': {
            'TITLE': f"{req['responsible'][5:]} {department_name} {req['file_id']}",
            'ufCrm15_1655883348': req['responsible'][5:],
            #'UF_CRM_15_1655883493': req['file_id'],
            #'UF_CRM_15_1655883421': department_name,
            }})
