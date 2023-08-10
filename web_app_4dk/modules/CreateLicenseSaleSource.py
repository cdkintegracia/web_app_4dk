from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def create_license_sale_source(req):
    dossier = b.get_all('crm.item.list', {
        'entityTypeId': '186',
        'filter': {
            'companyId': req['company_id']
        }
    })
    if dossier:
        seller = dossier[0]['ufCrm9_1655294863']
        dossier_id = dossier[0]['id']
        sale_source = dossier[0]['ufCrm9_1657715965']
    else:
        seller = '173'
    



#req = {'company_id': '13501'}
#create_license_sale_source(req)