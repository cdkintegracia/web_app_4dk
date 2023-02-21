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
    product_id = product_info['productRow']['productId']
    product_info = b.get_all('crm.product.get', {'id': product_id})
    if product_info['SECTION_ID'] not in ['219', '331']:
        b.call('im.notify.system.add', {
            'USER_ID': req['user_id'][5:],
            'MESSAGE': f'Используйте правильную номенклатуру для формирования договора ИТС'})
        return
    
