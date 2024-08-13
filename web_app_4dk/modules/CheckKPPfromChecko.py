from time import time
from datetime import datetime

from fast_bitrix24 import Bitrix
import requests
#from tabulate import tabulate

try:
    from authentication import authentication
except ModuleNotFoundError:
    from web_app_4dk.modules.authentication import authentication



b = Bitrix(authentication('Bitrix'))
checko_url = 'https://api.checko.ru/v2/'
api_key = 'jMw7CIIIJtOKSNUb'

def create_request(method: str, parameters: list) -> str:
    return f"{checko_url}{method}?key={api_key}&{'&'.join(parameters)}"

def get_result_values(result: dict) -> dict:

    if 'КПП' in result['data'] and result['data']['КПП']:
        company_kpp = result['data']['КПП']
        print(company_kpp)
    else:
        company_kpp = ''

    return {
        'КПП': company_kpp
    }

def check_kpp_from_checko(req):

    inn = req['inn']
    if len(inn) == 10:
        method = 'company'
        checko_request = requests.get(url=create_request(method, [f"inn={inn}"]))
        if checko_request.status_code == 200:
            result = checko_request.json()
            if 'message' not in result['meta']:

                values = get_result_values(result)
                q= b.call('bizproc.workflow.start', {
                        'TEMPLATE_ID': '2277',
                        'DOCUMENT_ID':['crm', 'CCrmDocumentDeal', 'DEAL_' + req['id_deal']],
                        'PARAMETERS': {
                            'kpp': values['КПП'],
                            }
                        })
                #print(q)


if __name__ == '__main__':
    req={
        'inn': '5638061980', 'id_deal': '124895'
    }
    check_kpp_from_checko(req)
