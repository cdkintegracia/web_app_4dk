"""Журнал трудозатрат Б24. По умолчанию только проверка; запись при APPLY = True."""

# НАСТРОЙКИ ЗАПУСКА — ключи командной строки не нужны.
APPLY = True  # False: только проверка. True: запись в Битрикс24.
COMPANY_ID = None  # Первая проверка. Для всех компаний установите None.
TASK_LOOKBACK_DAYS = 3  # До начала текущего месяца, а не до сегодняшнего дня.
NOTIFY_USER_ID = 1  # Получатель итогового уведомления в Битрикс24.

# Исключения ЭПД относятся только к группе 1 и точному тегу «ЭПД».
EPD_GROUP_ID = 1
EPD_TAG = 'ЭПД'
EXCLUDED_STAGE_IDS = {1767}  # «Завершена без решения», по диагностике группы 1.
COMPANY_EXCLUDE_FIELD = 'UF_CRM_1789223269972'  # «Не списывать ЭПД из лимита ЛК».


import copy
import logging
import re
import sys
from collections import defaultdict
from datetime import datetime, date, timedelta
from pathlib import Path
if __package__:
    from .worklog_common import API, config, values, scalar, duration, hms, list_lock, period_of, current_period, lock_file, accounting_timezone, month_name
else:
    from worklog_common import API, config, values, scalar, duration, hms, list_lock, period_of, current_period, lock_file, accounting_timezone, month_name

LOG = logging.getLogger('worklog')


def month_window(c):
    """Единый месяц всего прохода, границы в часовом поясе учёта."""
    period = c.get('_run_period') or current_period(c)
    start = datetime.fromisoformat(period + '-01').replace(tzinfo=accounting_timezone(c['timezone']))
    end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    return period, start, end, start - timedelta(days=TASK_LOOKBACK_DAYS)


def work_date(row, c):
    dt = datetime.fromisoformat(row['CREATED_DATE'].replace('Z','+00:00'))
    tz = accounting_timezone(c['timezone'])
    return dt.replace(tzinfo=tz) if dt.tzinfo is None else dt.astimezone(tz)


def company_of(task):
    ids={str(v)[3:] for v in values(task.get('ufCrmTask')) if re.fullmatch(r'CO_\d+',str(v))}
    if len(ids)!=1:
        raise ValueError('Нужна одна компания в CRM-привязке')
    return ids.pop()


def read_elapsed(api,tid):
    result,seen=[],set()
    page=1
    while True:
        rows=api.call('task.elapseditem.getlist',[int(tid),{'ID':'asc'},{},
            ['ID','TASK_ID','USER_ID','SECONDS','CREATED_DATE','COMMENT_TEXT'],
            {'NAV_PARAMS':{'nPageSize':50,'iNumPage':page}}])['result']
        if not isinstance(rows,list):raise ValueError('Некорректный ответ трудозатрат')
        for row in rows:
            if str(row['TASK_ID'])!=str(tid) or str(row['ID']) in seen:
                raise ValueError('Неполная/повторная страница трудозатрат')
            seen.add(str(row['ID']))
        result.extend(rows)
        if len(rows)<50:return result
        page+=1


def journal(api, c):
    # История журнала нужна для глобальной уникальности ключей, в том числе
    # когда дату существующей записи перенесли из другого месяца в текущий.
    # Исторические задачи по этим строкам повторно не опрашиваем.
    rows = api.pages(
        'crm.item.list',
        {
            'entityTypeId': c['entity_type_id'],
            'useOriginalUfNames': 'Y',
            'filter': {'categoryId': c['category_id']},
            'order': {'id': 'ASC'},
            'select': ['*'],
        },
        'items',
    )

    for row in rows:
        LOG.warning(
            'ЧТЕНИЕ ЖУРНАЛА: id=%r; ID=%r; '
            'companyId=%r; COMPANY_ID=%r',
            row.get('id'),
            row.get('ID'),
            row.get('companyId'),
            row.get('COMPANY_ID'),
        )

        if row.get('id') is None or row.get('companyId') is None:
            LOG.warning('ИМЕНА ПОЛЕЙ: %s', sorted(row.keys()))
            raise RuntimeError(
                'В ответе журнала отсутствует id или companyId; '
                'обработка остановлена до изменения данных'
            )

    return rows


def index_journal(items,c):
    f=c['fields'];out={}
    for row in items:
        key=row.get(f['key'])
        if not key:
            raise ValueError('В журнале есть элемент без ключа: '+str(row['id']))
        if key in out:raise ValueError('Дубли в журнале по ключу '+str(key))
        out[key]=row
    return out


def wanted_entry(tid,company,entry,rule,c):
    dt=work_date(entry,c)
    seconds=int(entry['SECONDS'])
    if seconds<0:raise ValueError('Отрицательная длительность')
    f=c['fields'];key=f'b24-task:{tid}:{entry["ID"]}'
    data={'source':c['source_id'],'key':key,'task':int(tid),'entry':int(entry['ID']),
        'group':rule['group_id'],'tag':rule['tag'],'direction':rule['direction_id'],
        'employee':int(entry['USER_ID']),'date':dt.isoformat(),'seconds':seconds,
        'description':entry.get('COMMENT_TEXT',''),'period':dt.strftime('%Y-%m'),
        'kind':rule['kind_id'],'state':c['active_state'],
        'url':f'https://vc4dk.bitrix24.ru/workgroups/group/{rule["group_id"]}/tasks/task/view/{tid}/'}
    fields={f[k]:v for k,v in data.items()}
    fields.update(companyId=int(company),categoryId=c['category_id'],
                  title=f'{rule["tag"]}: задача {tid}, запись {entry["ID"]}')
    return fields


def is_epd(group, tag):
    return str(group) == str(EPD_GROUP_ID) and tag == EPD_TAG


def company_excludes_epd(api, company, cache):
    """Кэш только одного прохода. Отсутствие поля/ошибка чтения — остановка."""
    if company not in cache:
        row = api.call('crm.company.get', {'id': int(company)})['result']
        if not isinstance(row, dict) or str(row.get('ID')) != str(company):
            raise RuntimeError('Не подтверждена компания ' + str(company))
        if COMPANY_EXCLUDE_FIELD not in row:
            raise RuntimeError('Компания %s: не получено поле %s' %
                               (company, COMPANY_EXCLUDE_FIELD))
        value = row[COMPANY_EXCLUDE_FIELD]
        # Пустое значение штатного поля «Да/Нет» означает, что отметка не стоит.
        if value is None or value is False or value == '' or type(value) is int and value == 0:
            excluded = False
        elif value is True or type(value) is int and value == 1:
            excluded = True
        elif isinstance(value, str) and value.strip().upper() in ('0', 'N', 'FALSE'):
            excluded = False
        elif isinstance(value, str) and value.strip().upper() in ('1', 'Y', 'TRUE'):
            excluded = True
        else:
            raise RuntimeError('Компания %s: некорректное значение поля %s' %
                               (company, COMPANY_EXCLUDE_FIELD))
        cache[company] = excluded
    return cache[company]


def prepare(api,c,old,company_filter=None,billing=None):
    """Полный сбор до первой записи. Сеть/невалидная дата прерывает весь проход."""
    f=c['fields'];selected={};rule_hits=defaultdict(list)
    if billing is None:billing={}
    company_cache={}
    period, month_start, month_end, task_start = month_window(c)
    previous=defaultdict(list)
    for key,row in old.items():
        if (str(row.get(f['source']))==str(c['source_id'])
                and row.get(f['period'])==period
                and (not company_filter or str(row.get('companyId'))==str(company_filter))):
            previous[str(row.get(f['task']))].append((key,row))

    def collect(rule, extra_filter, expected_ids=None):
        query={'GROUP_ID':rule['group_id'],'TAG':rule['tag']}
        query.update(extra_filter)
        tasks=api.pages('tasks.task.list',{'filter':query,
            'order':{'ID':'ASC'},'select':['ID','GROUP_ID','UF_CRM_TASK','STAGE_ID','CREATED_DATE']},'tasks')
        for task in tasks:
            tid=str(task['id'])
            if str(task.get('groupId'))!=str(rule['group_id']):
                raise ValueError('Ответ задачи не соответствует фильтру группы')
            if expected_ids is not None:
                if tid not in expected_ids:raise ValueError('Ответ задачи не соответствует фильтру ID')
            else:
                created=work_date({'CREATED_DATE':task['createdDate']},c)
                if not task_start<=created<month_end:
                    raise ValueError('Ответ задачи не соответствует фильтру даты создания')
            selected[tid]=task
            if rule not in rule_hits[tid]:rule_hits[tid].append(rule)

    for rule in c['rules']:
        collect(rule,{'>=CREATED_DATE':task_start.isoformat(),'<CREATED_DATE':month_end.isoformat()})
    recent_count=len(selected)
    # Только задачи из журнала ТЕКУЩЕГО месяца, не попавшие в отбор по дате.
    # Проверяем группу/тег заново, не принимаем сохранённые в журнале признаки за актуальные.
    missing=sorted(set(previous)-set(selected),key=int)
    for offset in range(0,len(missing),50):
        chunk=missing[offset:offset+50]
        for rule in c['rules']:
            collect(rule,{'ID':[int(tid) for tid in chunk]},set(chunk))
    LOG.info('Отбор %s: задачи созданы с %s до %s (не включая); по дате=%s; '
             'дополнительно из журнала=%s; не найдены=%s',
             period,task_start.isoformat(),month_end.isoformat(),recent_count,
             len(selected)-recent_count,len(set(previous)-set(selected)))
    target=copy.deepcopy(old);blocked=set();errors=[];processed=set()
    for tid in sorted(set(selected)|set(previous),key=int):
        old_rows=previous[tid]
        old_companies={str(r.get('companyId')) for _,r in old_rows}
        task=selected.get(tid)
        try:
            if task is None:raise ValueError('Задача исчезла из отбора: группа, тег, удаление или доступ')
            comp=company_of(task)
            if company_filter and comp!=str(company_filter) and str(company_filter) not in old_companies:continue
            if len(rule_hits[tid])!=1:raise ValueError('Задача подходит под несколько правил')
            rule=rule_hits[tid][0]
            if old_companies and old_companies!={comp}:raise ValueError('Компания учтённой задачи изменена')
            for _,r in old_rows:
                if str(r.get(f['group']))!=str(rule['group_id']) or r.get(f['tag'])!=rule['tag']:
                    raise ValueError('Группа или тег учтённой задачи изменены')
        except ValueError as exc:
            if company_filter and str(company_filter) not in old_companies:
                if not task:continue
                try:
                    if company_of(task)!=str(company_filter):continue
                except ValueError:continue
            blocked.update(old_companies)
            if task:
                try:blocked.add(company_of(task))
                except ValueError:pass
            errors.append(f'Задача {tid}: {exc}')
            for key,r in old_rows:target[key][f['state']]=c['review_state']
            continue
        # Не исключаем стадию из отбора задач: журнал хранит фактические записи,
        # а решение о списании заново принимается даже без изменения трудозатрат.
        if is_epd(rule['group_id'], rule['tag']):
            stage = task.get('stageId')
            if stage is None or not re.fullmatch(r'\d+', str(stage)):
                raise RuntimeError('Задача %s: не получена корректная стадия' % tid)
            company_excluded = company_excludes_epd(api, comp, company_cache)
            reasons = []
            if int(stage) in EXCLUDED_STAGE_IDS:
                reasons.append('стадия «Завершена без решения» (%s)' % stage)
            if company_excluded:
                reasons.append('отметка компании %s' % comp)
            billing[tid] = '; '.join(reasons)
        rows=read_elapsed(api,tid)
        processed.add(tid);seen=set()
        for entry in rows:
            dt=work_date(entry,c);key=f'b24-task:{tid}:{entry["ID"]}';seen.add(key)
            if not month_start<=dt<month_end or dt.date()<date.fromisoformat(c['start_date']):
                if key in target and target[key].get(f['period'])==period:
                    target[key][f['state']]=c['review_state']
                    target[key][f['seconds']]=0
                    target[key][f['date']]=dt.isoformat()
                    # Работа перенесена за границу месяца/до старта учёта: возвращаем
                    # списание текущего месяца. Старые месячные итоги не изменяем.
                continue
            fields=wanted_entry(tid,comp,entry,rule,c)
            target[key]=dict(target.get(key,{}),**fields)
        for key,r in old_rows:
            if key not in seen:target[key][f['state']]=c['deleted_state']
    LOG.info('Опрошено задач с трудозатратами: %s; месяц работ=%s',len(processed),period)
    return target,blocked,errors


def normalized(v):
    return '' if v is None else str(v)


def diff(old, new, c):
    fields = ['title', 'companyId', 'categoryId']
    fields += list(c['fields'].values())

    changes = {
        field: new[field]
        for field in fields
        if field in new
        and normalized(old.get(field)) != normalized(new[field])
    }

    for field, expected in changes.items():
        LOG.warning(
            'РАСХОЖДЕНИЕ: элемент=%s; поле=%s; '
            'ожидалось=%s; получено=%s',
            old.get('id'),
            field,
            repr(expected)[:300],
            repr(old.get(field))[:300],
        )

    return changes


def sync_journal(api,c,old,target):
    for key,row in target.items():
        prior=old.get(key)
        if prior is None:
            # Дополнительная проверка непосредственно перед добавлением.
            hits=api.pages('crm.item.list',{'entityTypeId':c['entity_type_id'],'useOriginalUfNames':'Y',
                'filter':{c['fields']['key']:key},'select':['id',c['fields']['key']]},'items')
            if hits:raise RuntimeError('Ключ появился после чтения журнала; повторите сверку: '+key)
            fields={k:v for k,v in row.items() if k!='id'}
            reply=api.call('crm.item.add',{'entityTypeId':c['entity_type_id'],
                'useOriginalUfNames':'Y','fields':fields},write=True)
            item=reply['result'].get('item',{})
            if not item.get('id'):raise RuntimeError('Не подтверждён ID новой записи журнала')
            row['id']=item['id']
        else:
            changes=diff(prior,row,c)
            if changes:
                api.call('crm.item.update',{'entityTypeId':c['entity_type_id'],'id':prior['id'],
                    'useOriginalUfNames':'Y','fields':changes},write=True)


def aggregate(items,c,blocked,billing=None,company_filter=None):
    f=c['fields'];sums=defaultdict(int);companies=set()
    period,month_start,month_end,_=month_window(c)
    for row in items.values():
        if row.get(f['period'])!=period:continue
        comp=str(row.get('companyId') or '')
        if not comp:continue
        if company_filter and comp!=str(company_filter):continue
        companies.add(comp)
        if comp in blocked:continue
        if str(row.get(f['kind']))!=str(c['general_kind']):continue
        if str(row.get(f['state']))!=str(c['active_state']):continue
        if str(row.get(f['employee'])) == '173':
            LOG.info(
                'Не включено в лимит: запись журнала=%s; '
                'сотрудник=173; секунд=%s',
                row.get('id'),
                row.get(f['seconds']),
            )
            continue
        if str(row.get(f['source'])) == str(c['source_id']) and is_epd(row.get(f['group']), row.get(f['tag'])):
            tid = str(row.get(f['task']))
            if billing is None or tid not in billing:
                raise RuntimeError('Задача %s: условия списания не проверены; публикация остановлена' % tid)
            if billing[tid]:
                LOG.info('Не включено в лимит: запись журнала=%s; задача=%s; секунд=%s; причина=%s',
                         row.get('id'), tid, row.get(f['seconds']), billing[tid])
                continue
        dt=work_date({'CREATED_DATE':str(row[f['date']])},c)
        if not month_start<=dt<month_end or dt.date()<date.fromisoformat(c['start_date']):continue
        seconds=int(row[f['seconds']])
        if seconds<0:raise ValueError('Отрицательные секунды в журнале')
        sums[(comp,str(row[f['period']]))]+=seconds
    return sums,companies


def publish(api,c,items,blocked,apply,company_filter=None,billing=None):
    f=c['fields'];sums,companies=aggregate(items,c,blocked,billing,company_filter);errors=[]
    run_period,_,_,_=month_window(c)
    for comp in sorted(companies,key=int):
        if company_filter and comp!=str(company_filter):continue
        if comp in blocked:
            LOG.warning('Компания %s: суммы заморожены до разбора задачи',comp);continue
        # История списка не пересчитывается. Строки текущего месяца с прежней
        # ненулевой суммой нужны и тогда, когда все трудозатраты теперь исключены.
        rows=api.pages('lists.element.get',dict(api.list_params(),FILTER={'PROPERTY_1299':comp,'NAME':month_name(run_period)}))
        by_period={}
        for r in rows:
            period=period_of(r)
            if period!=run_period:continue
            if period in by_period:raise ValueError(f'Дубли элементов {comp}/{period}')
            by_period[period]=r
        periods={p for co,p in sums if co==comp}
        periods.update(p for p,r in by_period.items() if duration(scalar(r,c['tasks_field']))>0)
        for period in sorted(periods):
            # Долгий проход мог пересечь полночь первого числа. Его результаты
            # нельзя публиковать как расход нового месяца.
            if apply and period != current_period(c):
                raise RuntimeError('Во время сбора сменился месяц; повторите запуск')
            if period not in by_period:
                errors.append(f'Нет месячного элемента {comp}/{period}; ' + ('часы сохранены в журнале' if apply else 'только проверка, записи не выполнялись'));continue
            with list_lock():
                row=api.get_element(by_period[period]['ID'])
                want=api.totals(row,{c['tasks_field']:hms(sums.get((comp,period),0))})
                api.preserved_fields(row)
                changed=any(normalized(scalar(row,k))!=normalized(v) for k,v in want.items())
                LOG.info('%s company=%s month=%s element=%s calls=%s tasks=%s total=%s changed=%s',
                    'APPLY' if apply else 'PREVIEW',comp,period,row['ID'],scalar(row,'PROPERTY_1303'),
                    want[c['tasks_field']],want[c['total_field']],changed)
                if apply and changed:
                    api.update_element(row,want)
                    check=api.get_element(row['ID'])
                    if any(normalized(scalar(check,k))!=normalized(v) for k,v in want.items()):
                        raise RuntimeError('Итоги не подтверждены повторным чтением')
            if apply:
                receiver=f'list:{c["list_id"]}:{row["ID"]}'
                for item in items.values():
                    if str(item.get('companyId'))==comp and item.get(f['period'])==period and str(item.get(f['kind']))==str(c['general_kind']):
                        if item.get(f['receiver'])!=receiver:
                            api.call('crm.item.update',{'entityTypeId':c['entity_type_id'],'useOriginalUfNames':'Y',
                                'id':item['id'],'fields':{f['receiver']:receiver}},write=True)
    return errors


def notify_completed(api, c, added, updated, errors, company_filter=None):
    """После подтверждения записей и публикации итогов. Ошибка доставки не отменяет загрузку."""
    status = ('Загрузка трудозатрат ЭПД завершена с ошибками.' if errors
              else 'Трудозатраты ЭПД успешно загружены.')
    scope = 'Все компании' if not company_filter else 'Компания %s' % company_filter
    message = (f'{status}\n'
               f'{scope}. Период: {c["_run_period"]}.\n'
               f'Журнал: обновлено {updated}, добавлено {added}.\n'
               f'Ошибки: {len(errors)}.')
    if errors:
        message += ' Подробности в журнале Flask.'
    try:
        # Тот же метод, который уже используется в FillActDocumentSmartProcess.
        # Без автоматического повтора при тайм-ауте: уведомление могло дойти.
        reply = api.call('im.notify.system.add',
                         {'USER_ID': NOTIFY_USER_ID, 'MESSAGE': message}, write=True)
        if not reply.get('result'):
            raise RuntimeError('Битрикс24 не подтвердил отправку уведомления')
        LOG.info('Итоговое уведомление отправлено пользователю %s', NOTIFY_USER_ID)
    except Exception:
        LOG.exception('Не удалось подтвердить доставку уведомления пользователю %s; '
                      'результат загрузки сохранён', NOTIFY_USER_ID)


def main():
    from types import SimpleNamespace
    args = SimpleNamespace(apply=APPLY, company=COMPANY_ID)
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
    LOG.setLevel(logging.INFO)
    LOG.info('Режим: %s; компания: %s', 'ЗАПИСЬ' if APPLY else 'ПРОВЕРКА БЕЗ ЗАПИСИ', COMPANY_ID or 'все')
    c=config();c['_run_period']=current_period(c)
    api=API(c);api.validate_fields();date.fromisoformat(c['start_date'])
    schema=api.call('crm.item.fields',{'entityTypeId':c['entity_type_id'],'useOriginalUfNames':'Y'})['result']['fields']
    for key in c['fields'].values():
        if key not in schema:raise ValueError('Отсутствует поле журнала '+key)
    path=Path(c['sync_lock_path']);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a+b') as lock:
        try:lock_file(lock)
        except BlockingIOError:
            LOG.info('Предыдущий сборщик ещё работает');return 3
        old=index_journal(journal(api,c),c)
        billing={}
        target,blocked,errors=prepare(api,c,old,args.company,billing)
        new_count=sum(k not in old for k in target)
        edit_count=sum(bool(diff(old[k],v,c)) for k,v in target.items() if k in old)
        LOG.info('Журнал: новых=%s, изменений=%s, дата начала=%s',new_count,edit_count,c['start_date'])
        for msg in errors:LOG.warning(msg)
        if args.apply:
            if current_period(c)!=c['_run_period']:
                raise RuntimeError('Во время сбора сменился месяц; повторите запуск')
            sync_journal(api,c,old,target)
            actual=index_journal(journal(api,c),c)
            for key,row in target.items():
                if key not in actual or diff(actual[key],row,c):
                    raise RuntimeError('Журнал не подтвердил записанные данные; публикация отложена')
            target=actual
        errors+=publish(api,c,target,blocked,args.apply,args.company,billing)
        for msg in errors:LOG.warning(msg)
        LOG.info('Завершено. Исключений: %s',len(errors))
        if args.apply:
            notify_completed(api,c,new_count,edit_count,errors,args.company)
        return 2 if errors else 0


def sync_worklog(req=None):
    """Обычная функция для routes.py. Расчёт выполняется до возврата HTTP-ответа."""
    mode = 'ЗАПИСЬ' if APPLY else 'ПРОВЕРКА БЕЗ ЗАПИСИ'
    try:
        code = main()
    except Exception:
        LOG.exception('Ошибка учёта трудозатрат')
        return 'Ошибка учёта трудозатрат. Подробности в журнале Flask.\n', 500
    if code == 3:
        return 'Учёт уже выполняется. Повторный запуск пропущен.\n', 200
    if code != 0:
        return f'{mode}: обработка завершена с исключениями. Проверьте журнал Flask.\n', 500
    return f'OK. {mode}. Компания: {COMPANY_ID or "все"}. Обработка завершена без ошибок.\n', 200


if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:
        logging.error('%s: %s',type(exc).__name__,exc)
        sys.exit(1)
