from fast_bitrix24 import Bitrix

try:
    from authentication import authentication
except ModuleNotFoundError:
    from web_app_4dk.modules.authentication import authentication


def check_product_nomenclature(req):
    products = req['products']
    print(products)
