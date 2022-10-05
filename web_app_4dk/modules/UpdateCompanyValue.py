from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication

# Считывание файла authentication.txt

webhook = authentication('Bitrix')
b = Bitrix(webhook)


def update_company_value(req):
    """
    :param req: request.form
    :return: Обновление поля "Вес сделок" в компании в случае удаления сделки
    """
    deal_id = req['data[FIELDS][ID]']

    """
    :param deal_id: ID удаленной сделки
    :return: Запуск БП "Вес сделок" с новым значением поля "Вес компании"
    """

    # Нахождение компании, к которой привязана сделка
    try:
        company = b.get_all(
            'crm.company.list', {
                'filter': {'UF_CRM_1660824010': deal_id}
            }
        )[0]['ID']
    except:
        return
    company_id = f'COMPANY_{company}'

    # Запуск БП "Вес сделок"

    b.call('bizproc.workflow.start', {
        'TEMPLATE_ID': '1031',
        'DOCUMENT_ID': ['crm', 'CCrmDocumentCompany', company_id],
        'PARAMETERS': {'process': 'Удаление', 'src': deal_id, 'new_value': '1'}
    }
           )