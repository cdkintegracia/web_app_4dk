from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def create_95_service_using_task(req):
    text = ''
    for key, value in req.items():
        text += key, '', value, '\n'
    b.call('im.notify.system.add', {
        'USER_ID': '311',
        'MESSAGE': text})