from fast_bitrix24 import Bitrix

try:
    from authentication import authentication
except ModuleNotFoundError:
    from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def get_regnumber_elements(req):
    regnumber_elements = b.get_all('lists.element.get', {
        'IBLOCK_TYPE_ID': 'lists',
        'IBLOCK_ID': '31',
        'filter': {
            'PROPERTY_123': req['company_id']
        }
    })
    regnumbers_info = ''
    for element in regnumber_elements:
        regnumbers_info += f'{element["NAME"]}\n\n'

    b.call('bizproc.workflow.start', {
        'TEMPLATE_ID': '1467',
        'DOCUMENT_ID': ['crm', 'CCrmDocumentDeal', 'DEAL_' + req['deal_id']],
        'PARAMETERS': {
            'regnumbers': regnumbers_info,
        }
    })
