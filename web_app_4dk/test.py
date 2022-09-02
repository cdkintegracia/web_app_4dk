from fast_bitrix24 import Bitrix

b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')

b.call('bizproc.workflow.start', {
        'TEMPLATE_ID': '1095',
        'DOCUMENT_ID':
            ['lists', 'BizprocDocument', '128131'],
        'PARAMETERS': {'user': '311', 'message': f"Сверка ИТС завершена"}})