from fast_bitrix24 import Bitrix

from authentication import authentication


b = Bitrix(authentication('Bitrix'))

'''
elements = b.get_all('crm.item.list', {
        'entityTypeId': '161',
    })

companies = list(map(lambda x: x['companyId'], elements))
companies = b.get_all('crm.company.list', {
    'filter': {
        'ID': companies
    }
})

for element in elements:
    update_fields = dict()
    company = list(filter(lambda x: str(x['ID']) == str(element['companyId']), companies))
    if company:
        update_fields['ufCrm41_1690546413'] = company[0]['TITLE']

    update_fields['ufCrm41_1690807843'] = int(element['ufCrm41_1689101306'].split('-')[-1])
    b.call('crm.item.update', {
        'entityTypeId': '161',
        'id': element['id'],
        'fields': update_fields
    })
'''
users = b.get_all('user.get', {
        'filter': {
            '!UF_USR_1690373869887': None
        }
    })
for user in users:
    print(user)
