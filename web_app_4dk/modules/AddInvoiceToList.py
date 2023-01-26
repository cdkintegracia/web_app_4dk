from time import time

from fast_bitrix24 import Bitrix
import requests

from web_app_4dk.modules.authentication import authentication

b = Bitrix(authentication('Bitrix'))


def add_invoice_to_list(req):
    r = requests.get(f"{authentication('Bitrix')}crm.documentgenerator.document.list?filter[entityTypeId]=31&filter[entityId]={req['id']}").json()
    if not 'result' in r:
        return
    for document in r['result']['documents']:
        b.call('lists.element.add', {
            'IBLOCK_TYPE_ID': 'lists',
            'IBLOCK_ID': '241',
            'ELEMENT_CODE': time(),
            'fields': {
                'NAME': document['number'],
                'PROPERTY_1595': '',
                'PROPERTY_1597': req['id'],
            }
        })

