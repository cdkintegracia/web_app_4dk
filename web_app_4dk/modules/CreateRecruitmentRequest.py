from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def create_recruitment_request(req):
    department_info = b.get_all('department.get', {'ID': req['department'][0]})
    print(department_info['NAME'])
