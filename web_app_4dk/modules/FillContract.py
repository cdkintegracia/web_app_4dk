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
    b.call('im.notify.system.add', {
        'USER_ID': '311',
        'MESSAGE': f'{cased_ln} {cased_fn} {cased_sn}'})