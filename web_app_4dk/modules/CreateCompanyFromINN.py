from time import time
from datetime import datetime

from fast_bitrix24 import Bitrix
import requests
#from tabulate import tabulate

from authentication import authentication



b = Bitrix(authentication('Bitrix'),ssl=False)
checko_url = 'https://api.checko.ru/v2/'
api_key = 'jMw7CIIIJtOKSNUb'

def create_request(method: str, parameters: list) -> str:
    return f"{checko_url}{method}?key={api_key}&{'&'.join(parameters)}"

def get_result_values(result: dict) -> dict:

    if 'КПП' in result['data'] and result['data']['КПП']:
        company_kpp = result['data']['КПП']
    else:
        company_kpp = ''
    if 'НаимСокр' in result['data'] and result['data']['НаимСокр']:
        company_naimsokr = result['data']['НаимСокр']
    if 'ФИО' in result['data'] and result['data']['ФИО']:
        company_naimsokr = result['data']['ТипСокр'] + ' ' + result['data']['ФИО']


    return {
        'КПП': company_kpp,
        'НаимСокр': company_naimsokr
    }

def create_company_from_inn(req):

    company_info = req['company_info']
    if len(company_info) == 10:
        method = 'company'
        checko_request = requests.get(url=create_request(method, [f"inn={company_info}"]))
        if checko_request.status_code == 200:
            result = checko_request.json()
            if 'message' not in result['meta']:

                values = get_result_values(result)
                q= b.call('crm.company.add', {
                    'fields':{
                        'TITLE': values['НаимСокр'],
                        'UF_CRM_1656070716':company_info
                            }
                        })
                new_company_id = q['order0000000000']
                b.call('crm.requisite.add', {
                    'fields':{
                        'ENTITY_TYPE_ID':4,
                        'ENTITY_ID':new_company_id,
                        'PRESET_ID':1,
                        'NAME': values['НаимСокр'],
                        'ACTIVE':'Y',
                        'RQ_INN': company_info,
                        'RQ_KPP': values['КПП']
                        }
                    })

                b.call('crm.deal.update', {
                    'ID': req['deal_id'],
                    'fields': {
                        'UF_CRM_1712668987 ': new_company_id,
                        'STAGE_ID': 'UC_0XG0S5'
                        }
                    })

    elif len(company_info) == 12:
        method = 'entrepreneur'
        checko_request = requests.get(url=create_request(method, [f"inn={company_info}"]))
        if checko_request.status_code == 200:
            result = checko_request.json()
            if 'message' not in result['meta']:
                values = get_result_values(result)
                q =b.call('crm.company.add', {
                    'fields':{
                        'TITLE': values['НаимСокр'],
                        'UF_CRM_1656070716':company_info
                            }
                        })

                new_company_id = q['order0000000000']
                b.call('crm.requisite.add', {
                    'fields':{
                        'ENTITY_TYPE_ID':4,
                        'ENTITY_ID':new_company_id,
                        'PRESET_ID':3,
                        'NAME': values['НаимСокр'],
                        'ACTIVE':'Y',
                        'RQ_INN': company_info
                        }
                    })

                b.call('crm.deal.update', {
                    'ID': req['deal_id'],
                    'fields': {
                        'UF_CRM_1712668987 ': new_company_id,
                        'STAGE_ID': 'UC_0XG0S5'
                        }
                    })

if __name__ == '__main__':
    create_company_from_inn()
