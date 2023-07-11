from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication
from web_app_4dk.tools import send_bitrix_request


b = Bitrix(authentication('Bitrix'))


def add_invoice_number(req):

    documents = send_bitrix_request('crm.documentgenerator.document.list', {
        'filter': {
            'entityTypeId': '31',
            'entityId': req['id']
        }
    })
    document_number = documents['documents'][-1]['number']
    b.call('crm.item.update', {
        'entityTypeId': '31',
        'id': req['id'],
        'fields': {
            'ufCrm_SMART_INVOICE_1684919199892': f"{req['invoice_title']} {document_number}",
        }
    })
