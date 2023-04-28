from time import sleep

from fast_bitrix24 import Bitrix

from authentication import authentication


b = Bitrix(authentication('Bitrix'))

'''
elements = b.get_all('lists.element.get', {
        'IBLOCK_TYPE_ID': 'lists',
        'IBLOCK_ID': '175',
        'filter': {
            'PROPERTY_1339': ['2219', '2221']
        }
})
counter = 0
for el in elements:
    counter += 1
    print(counter)
    b.call('bizproc.workflow.start', {
        'TEMPLATE_ID': '1509',
        'DOCUMENT_ID': ['lists', 'Bitrix\Lists\BizprocDocumentLists', el['ID']]
    })
'''
elements = b.get_all('lists.element.get', {
        'IBLOCK_TYPE_ID': 'lists',
        'IBLOCK_ID': '109',
})
counter = 0
for el in elements:
    counter += 1
    print(counter)
    b.call('bizproc.workflow.start', {
        'TEMPLATE_ID': '1065',
        'DOCUMENT_ID': ['lists', 'Bitrix\Lists\BizprocDocumentLists', el['ID']]
    })
    sleep(10)