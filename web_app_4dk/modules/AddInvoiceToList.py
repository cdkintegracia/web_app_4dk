from fast_bitrix24 import Bitrix

from authentication import authentication

b = Bitrix(authentication('Bitrix'))


def add_invoice_to_list(req):
    print(req)