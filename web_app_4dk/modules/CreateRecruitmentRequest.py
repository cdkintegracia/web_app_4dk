from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def create_recruitment_request(req):
    b.call('crm.item.add', {
        'entityTypeId': '130',
        'fields': {
            'ufCrm15_1655883348': req['responsible'][5:],
            'ufCrm15_1675868673': req['file_url'],
            'ufCrm15_1655883421': req['department'],
            }})
