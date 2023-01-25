from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication
import requests

b = Bitrix(authentication('Bitrix'))


def add_invoice_to_list(req):
    data = {'order': {'id': 'desc'}, 'filter': {'entityTypeId': req['id']}}
    documents_info = requests.post(url=f"{authentication('Bitrix')}crm.documentgenerator.document.list").json()['result']['documents']
    for document in documents_info:
        print(document['id'])
