import builtins

from fast_bitrix24 import Bitrix

try:
    from authentication import authentication
except ModuleNotFoundError:
    from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def check_product_nomenclature(req):
    product_id = req['product']
    product_info = b.get_all('crm.item.productrow.get', {'id': product_id})
    product_nomenclature = product_info['productRow']['productId']
    product_info = b.get_all('crm.product.get', {'id': product_nomenclature})
    if product_info['SECTION_ID'] not in [
        '219',  # Земля
        '331'   # Облако
    ]:
        b.call('im.notify.system.add', {
            'USER_ID': req['user_id'][5:],
            'MESSAGE': f'Используйте правильную номенклатуру для формирования договора ИТС'})
        return
    b.call('bizproc.workflow.start', {
        'TEMPLATE_ID': '1433',
        'DOCUMENT_ID': ['crm', 'CCrmDocumentDeal', 'DEAL_' + req['deal_id']],
        'PARAMETERS': {
            'document_type': req['document_type'],
        }
    })

