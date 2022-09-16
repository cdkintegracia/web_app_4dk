from fast_bitrix24 import Bitrix

from web_app_4dk.authentication import authentication

b = Bitrix(authentication('Bitrix'))

def create_deal():

    ignore_fields = [
        'ID',
        'TITLE',
        'TYPE_ID',
        'CATEGORY_ID',
        'STAGE_ID',
        'STAGE_SEMANTIC_ID',
        'IS_NEW',
        'IS_RECURRING',
        'IS_RETURN_CUSTOMER',
        'IS_REPEATED_APPROACH',
        'PROBABILITY',
        'CURRENCY_ID',
        'OPPORTUNITY',
        'IS_MANUAL_OPPORTUNITY',
        'TAX_VALUE',
        'COMPANY_ID',
        'CONTACT_IDS',
        'QUOTE_ID',
        'BEGINDATE',
        'CLOSEDATE',
        'OPENED',
        'CLOSED',
        'COMMENTS',
        'ASSIGNED_BY_ID',
        'CREATED_BY_ID',
        'MODIFY_BY_ID',
        'MOVED_BY_ID',
        'DATE_CREATE',
        'DATE_MODIFY',
        'MOVED_TIME',
        'SOURCE_ID',
        'SOURCE_DESCRIPTION',
        'LEAD_ID',
        'ADDITIONAL_INFO',
        'LOCATION_ID',
        'ORIGINATOR_ID',
        'ORIGIN_ID',
        'CONTACT_ID',
        'UTM_SOURCE',
        'UTM_MEDIUM',
        'UTM_CAMPAIGN',
        'UTM_CONTENT',
        'UTM_TERM',
        'UF_CRM_1638105792053',     # Дата начала действия пакета
        'UF_CRM_1637933869479',     # Автопролонгация
        'UF_CRM_1640523703',        # Подразделение
        'UF_CRM_1644140210142',     # Доступность ЛК
        'UF_CRM_1643800749',        # Регистрация подписки в 1С
        'UF_CRM_1657878818384',     # Группа
        'UF_CRM_1662365565770',     # Помощник
        'UF_CRM_1638105694957',     # E-mail регистрации
        'UF_CRM_1644508990370',     # Регномер Фреша
        'UF_CRM_1637933934722',     # Способ обслуживания
        'COMMENTS',
    ]
    deal_fields = b.get_all('crm.deal.fields')
    fields_to_clear = {}
    for field in deal_fields.keys():
        if field not in ignore_fields:
            fields_to_clear.setdefault(field, '')
    b.call('crm.deal.update', {'ID': '106603', 'fields': fields_to_clear})



if __name__ == '__main__':
    create_deal()