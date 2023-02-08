from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def create_recruitment_request(req):
    print(req)
