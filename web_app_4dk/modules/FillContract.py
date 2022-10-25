from petrovich.main import Petrovich
from petrovich.enums import Case


def fill_contract(req):
    p = Petrovich()
    cased_fn = p.firstname(req['first_name'], Case.GENITIVE)
    cased_ln = p.lastname(req['last_name'], Case.GENITIVE)
    cased_sn = p.middlename(req['second_name'], Case.GENITIVE)
    print(cased_ln, cased_fn, cased_sn)