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
    invoice_info = b.get_all('crm.item.get', {
        'entityTypeId': '31',
        'id': req['id'],
    })
    b.call('crm.item.update', {
        'entityTypeId': '31',
        'id': req['id'],
        'fields': {
            'ufCrm_SMART_INVOICE_1684919199892': f"{invoice_info['item']['title']} {document_number}",
            'ufCrm_SMART_INVOICE_1691071952214': document_number,
            'ufCrm_SMART_INVOICE_3862188824191':document_number
        }
    })
