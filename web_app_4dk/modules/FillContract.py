import pymorphy2
from petrovich.main import Petrovich
from petrovich.enums import Case, Gender
from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


def fill_contract(req):
    b = Bitrix(authentication('Bitrix'))
    p = Petrovich()
    morph = pymorphy2.MorphAnalyzer(lang='ru')
    genders = {
        'Мужской': Gender.MALE,
        'Женский': Gender.FEMALE,
        'Не указано': Gender.ANDRGN
    }
    cased_fn = p.firstname(req['first_name'], Case.GENITIVE, genders[req['gender']])
    cased_ln = p.lastname(req['last_name'], Case.GENITIVE, genders[req['gender']])
    cased_sn = p.middlename(req['second_name'], Case.GENITIVE, genders[req['gender']])
    job_post = []
    try:
        for word in req['job_post'].split():
            parse_word = morph.parse(word)[0]
            cased_word = parse_word.inflect({'gent'})
            job_post.append(cased_word[0])
        cased_job_post = ' '.join(job_post)
    except:
        cased_job_post = req['job_post']
    b.call('bizproc.workflow.start', {
        'TEMPLATE_ID': '1203',
        'DOCUMENT_ID': ['crm', 'CCrmDocumentDeal', 'DEAL_' + req['deal_id']],
        'PARAMETERS': {
            'fio': f"{req['last_name'].upper()} {req['first_name'][0].upper()}. {req['second_name'][0].upper()}.",
            'cased_fio': f"{cased_ln.upper()} {cased_fn.upper()} {cased_sn.upper()}",
            'type': req['type'],
            'based': req['based'].capitalize(),
            'job_post': req['job_post'].capitalize(),
            'cased_job_post': cased_job_post.lower(),
        }})
