from petrovich.main import Petrovich
from petrovich.enums import Case

from web_app_4dk.modules.authentication import authentication


def fill_contract(req):
    b = authentication('Bitrix')
    p = Petrovich()
    cased_fn = p.firstname(req['first_name'], Case.GENITIVE)
    cased_ln = p.lastname(req['last_name'], Case.GENITIVE)
    cased_sn = p.middlename(req['second_name'], Case.GENITIVE)
    b.call('im.notify.system.add', {
        'USER_ID': '311',
        'MESSAGE': f'{cased_ln}, {cased_fn} {cased_sn}'})
    print(cased_ln, cased_fn, cased_sn)