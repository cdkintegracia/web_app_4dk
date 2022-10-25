from petrovich.main import Petrovich
from petrovich.enums import Case, Gender
from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


def fill_contract(req):
    b = Bitrix(authentication('Bitrix'))
    p = Petrovich()
    genders = {
        'Мужской': Gender.MALE,
        'Женский': Gender.FEMALE,
        'Не указано': Gender.ANDRGN
    }
    cased_fn = p.firstname(req['first_name'], Case.GENITIVE, genders[req['gender']])
    cased_ln = p.lastname(req['last_name'], Case.GENITIVE, genders[req['gender']])
    cased_sn = p.middlename(req['second_name'], Case.GENITIVE, genders[req['gender']])
    b.call('bizproc.workflow.start', {
        'TEMPLATE_ID': '1203',
        'DOCUMENT_ID': ['crm', 'CCrmDocumentDeal', 'DEAL_' + req['deal_id']],
        'PARAMETERS': {
            'fio': f"{req['last_name']} {req['first_name']} {req['second_name']}",
            'cased_fio': f"{cased_ln} {cased_fn} {cased_sn}",
            'type': req['type']
        }})
