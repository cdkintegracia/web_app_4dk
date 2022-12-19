from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def create_info_smart_process(req):
    element_id = req['element_id']
    element_info = b.get_all('lists.element.get',  {
            'IBLOCK_TYPE_ID': 'lists',
            'IBLOCK_ID': '233',
            'ELEMENT_ID': element_id
    })[0]
    element_company = list(element_info['PROPERTY_1557'].values())[0]
    element_contact = list(element_info['PROPERTY_1559'].values())[0]
    element_comment = f"Проблемы и пожелания: {list(element_info['PROPERTY_1539'].values())[0]['TEXT'].replace('<br>', ' ')}\n" \
                      f"Смена ЭЦП: {list(element_info['PROPERTY_1553'].values())[0]}\n" \
                      f"Долги по ЭДО: {list(element_info['PROPERTY_1555'].values())[0]}\n" \
                      f"Опрос по КС: {list(element_info['PROPERTY_1561'].values())[0]['TEXT'].replace('<br>', ' ')}\n"
    b.call('crm.item.add', {'entityTypeId': '141', 'fields': {'companyId': element_company, 'contactId': element_contact, 'ufCrm25_1666342439': element_comment}})

