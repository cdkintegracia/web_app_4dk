from time import time

from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def go3_task_handler(req):
    yes_symbols = ['+', 'д', 'Д']
    no_symbols = ['-', 'н', 'Н']
    go3_field_value = ''
    for symbol in yes_symbols:
        if symbol in req['go3']:
            go3_field_value = '1555'
            break

    if not go3_field_value:
        for symbol in no_symbols:
            if symbol in req['go3']:
                go3_field_value = '1557'
                break

    if go3_field_value:
        task_info = b.get_all('tasks.task.get', {
            'taskId': req['task_id'],
            'select': ['*', 'UF_*'],
        })['task']
        uf_crm_company = list(filter(lambda x: 'CO_' in x, task_info['ufCrmTask']))[0]
        company_id = uf_crm_company[3:]
        b.call('crm.company.update', {
            'ID': company_id,
            'fields': {
                'UF_CRM_1688113081779': go3_field_value
            }
        })

        b.call('lists.element.add', {
            'IBLOCK_TYPE_ID': 'lists',
            'IBLOCK_ID': '275',
            'ELEMENT_CODE': time(),
            'fields': {
                'NAME': req['task_name'].split(' летние продажи 2023')[0],
                'PROPERTY_1737': req['responsible_id'],
                'PROPERTY_1733': company_id,
                'PROPERTY_1735': '2723' if go3_field_value == '1555' else '2725'
            }
        })
