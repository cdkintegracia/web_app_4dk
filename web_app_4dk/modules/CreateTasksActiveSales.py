from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication

b = Bitrix(authentication('Bitrix'))


def create_tasks_active_sales(req):
    companies_id = req['companies_id'].split(' ')
    for company in companies_id:
        print(company)