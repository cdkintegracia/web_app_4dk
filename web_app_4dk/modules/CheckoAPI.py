from fast_bitrix24 import Bitrix
import requests

from authentication import authentication


b = Bitrix(authentication('Bitrix'))
checko_url = 'https://api.checko.ru/v2/'
api_key = 'eF5kqvvyrN2eqCaU'
api_methods = ['finances', 'company', 'entrepreneur']


def create_request(method:str, parameters:list) -> str:
    return f"{checko_url}{method}?key={api_key}&{'&'.join(parameters)}"


def get_info_from_checko():
    errors = []
    inn = '7842117940'
    for method in api_methods:
        checko_request = requests.get(url=create_request(method, [f'inn={inn}']))
        if checko_request.status_code == 200:
            result = checko_request.json()
            print(result)
            #if method == 'finances':

        else:
            errors.append(inn)

get_info_from_checko()

