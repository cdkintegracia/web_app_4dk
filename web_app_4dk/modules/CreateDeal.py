from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication

b = Bitrix(authentication('Bitrix'))

def create_deal(req):

    ignore_fields = [
        'ID',       # ID
        'TITLE',        # Название
        'TYPE_ID',      # Тип
        'CATEGORY_ID',      # Направление
        'STAGE_ID',     # Стадия сделки
        'STAGE_SEMANTIC_ID',        # Группа стадии
        'IS_NEW',       # Новая сделка
        'IS_RECURRING',     # Регулярная сделка
        'IS_RETURN_CUSTOMER',       # Повторная сделка
        'IS_REPEATED_APPROACH',     # Повторное обращение
        'PROBABILITY',      # Вероятность
        'CURRENCY_ID',      # Валюта
        'OPPORTUNITY',      # Сумма
        'IS_MANUAL_OPPORTUNITY',
        'TAX_VALUE',        # Ставка налога
        'COMPANY_ID',       # Компания
        'CONTACT_IDS',      # Контакты
        'QUOTE_ID',     # Предложение
        'BEGINDATE',        # Дата начала
        'CLOSEDATE',        # Дата завершения
        'OPENED',       # Доступна для всех
        'CLOSED',       # Закрыта
        'COMMENTS',     # Комментарий
        'ASSIGNED_BY_ID',       # Ответственный
        'CREATED_BY_ID',        # Кем создана
        'MODIFY_BY_ID',     # Кем изменена
        'MOVED_BY_ID',
        'DATE_CREATE',      # Дата создания
        'DATE_MODIFY',      # Дата изменения
        'MOVED_TIME',
        'SOURCE_ID',        # Источник
        'SOURCE_DESCRIPTION',       # Дополнительно об источнике
        'LEAD_ID',      # Лид
        'ADDITIONAL_INFO',      # Дополнительная информация
        'LOCATION_ID',      # Местоположение
        'ORIGINATOR_ID',        # Внешний источник
        'ORIGIN_ID',        # Идентификатор элемента во внешнем источнике
        'CONTACT_ID',       # Контакт
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
        'UF_CRM_1640523562691',     # Регномер
        'UF_CRM_1637934121',        # ГК
        'UF_CRM_1637934192647',     # Конфа
        'UF_CRM_1637934330556',     # Срок действия ЭЦП
        'UF_CRM_1637934357592',     # Вендор ЭЦП
        'UF_CRM_1638282502',        # Сервис-менеджер
        'UF_CRM_1651149324',        # Оплачено от
        'UF_CRM_1638100416',        # Сроки подписки
        'UF_CRM_1651071211',        # Льготная отчетность
        'UF_CRM_1638958630625',     # Дата проверки оплаты
        'UF_CRM_1642775558379',     # Способ оплаты
        ''
    ]

    deal_fields = b.get_all('crm.deal.fields')
    fields_to_clear = {}
    for field in deal_fields.keys():
        if field not in ignore_fields:
            fields_to_clear.setdefault(field, '')
    b.call('crm.deal.update', {'ID': req['data[FIELDS][ID]'], 'fields': fields_to_clear})



if __name__ == '__main__':
    create_deal()