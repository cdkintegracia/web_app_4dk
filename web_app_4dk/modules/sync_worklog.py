"""Журнал трудозатрат Б24. По умолчанию только проверка; запись при APPLY = True."""

# НАСТРОЙКИ ЗАПУСКА — ключи командной строки не нужны.
APPLY = False  # False: только проверка. True: запись в Битрикс24.
COMPANY_ID = 1475  # Первая проверка. Для всех компаний установите None.


import copy
import logging
import re
import sys
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path
if __package__:
    from .worklog_common import API, config, values, scalar, duration, hms, list_lock, period_of, current_period, lock_file, accounting_timezone
else:
    from worklog_common import API, config, values, scalar, duration, hms, list_lock, period_of, current_period, lock_file, accounting_timezone

LOG = logging.getLogger('worklog')


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


def journal(api,c):
    return api.pages('crm.item.list',{'entityTypeId':c['entity_type_id'],
        'useOriginalUfNames':'Y','filter':{'categoryId':c['category_id']},
        'order':{'id':'ASC'},'select':['id','title','companyId','categoryId']+list(c['fields'].values())},'items')


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


def prepare(api,c,old,company_filter=None):
    """Полный сбор до первой записи. Сеть/невалидная дата прерывает весь проход."""
    f=c['fields'];selected={};rule_hits=defaultdict(list)
    for rule in c['rules']:
        tasks=api.pages('tasks.task.list',{'filter':{'GROUP_ID':rule['group_id'],'TAG':rule['tag']},
            'order':{'ID':'ASC'},'select':['ID','GROUP_ID','UF_CRM_TASK']},'tasks')
        for task in tasks:
            tid=str(task['id'])
            if str(task.get('groupId'))!=str(rule['group_id']):
                raise ValueError('Ответ задачи не соответствует фильтру группы')
            selected[tid]=task;rule_hits[tid].append(rule)
    target=copy.deepcopy(old);blocked=set();errors=[];processed=set()
    previous=defaultdict(list)
    for key,row in old.items():
        if str(row.get(f['source']))==str(c['source_id']):
            previous[str(row.get(f['task']))].append((key,row))
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
        rows=read_elapsed(api,tid)
        processed.add(tid);seen=set()
        for entry in rows:
            dt=work_date(entry,c);key=f'b24-task:{tid}:{entry["ID"]}';seen.add(key)
            if dt.date()<date.fromisoformat(c['start_date']):
                if key in target:
                    target[key][f['state']]=c['review_state']
                    target[key][f['seconds']]=0
                    target[key][f['date']]=dt.isoformat()
                    # Старый period оставлен для объяснения корректировки; сбор не учитывает дату до X.
                continue
            fields=wanted_entry(tid,comp,entry,rule,c)
            target[key]=dict(target.get(key,{}),**fields)
        for key,r in old_rows:
            if key not in seen:target[key][f['state']]=c['deleted_state']
    return target,blocked,errors


def normalized(v):
    return '' if v is None else str(v)


def diff(old,new,c):
    fields=['title','companyId','categoryId']+list(c['fields'].values())
    return {k:new[k] for k in fields if k in new and normalized(old.get(k))!=normalized(new[k])}


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


def aggregate(items,c,blocked):
    f=c['fields'];sums=defaultdict(int);companies=set()
    for row in items.values():
        comp=str(row.get('companyId') or '')
        if not comp:continue
        companies.add(comp)
        if comp in blocked:continue
        if str(row.get(f['kind']))!=str(c['general_kind']):continue
        if str(row.get(f['state']))!=str(c['active_state']):continue
        dt=datetime.fromisoformat(str(row[f['date']]).replace('Z','+00:00'))
        if dt.date()<date.fromisoformat(c['start_date']):continue
        seconds=int(row[f['seconds']])
        if seconds<0:raise ValueError('Отрицательные секунды в журнале')
        sums[(comp,str(row[f['period']]))]+=seconds
    return sums,companies


def publish(api,c,items,blocked,apply,company_filter=None):
    f=c['fields'];sums,companies=aggregate(items,c,blocked);errors=[]
    for comp in sorted(companies,key=int):
        if company_filter and comp!=str(company_filter):continue
        if comp in blocked:
            LOG.warning('Компания %s: суммы заморожены до разбора задачи',comp);continue
        # Читаем историю только затронутых компаний: это восстанавливает старый месяц
        # после переноса даты, даже если прошлый запуск оборвался после изменения журнала.
        rows=api.pages('lists.element.get',dict(api.list_params(),FILTER={'PROPERTY_1299':comp}))
        by_period={}
        for r in rows:
            period=period_of(r)
            if period in by_period:raise ValueError(f'Дубли элементов {comp}/{period}')
            by_period[period]=r
        periods={p for co,p in sums if co==comp}
        periods.update(p for p,r in by_period.items() if duration(scalar(r,c['tasks_field']))>0)
        for period in sorted(periods):
            # В исходных БП остаток компании не привязан к месяцу, а годовой учёт
            # использует один LAST_DURATIONS. Автопубликация старого месяца способна
            # повредить текущий остаток. Такие записи остаются в журнале до доработки БП.
            if apply and period != current_period(c):
                errors.append(f'Отложено {comp}/{period}: публикация другого месяца требует отдельной сверки месячного/годового остатка')
                continue
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


def main():
    from types import SimpleNamespace
    args = SimpleNamespace(apply=APPLY, company=COMPANY_ID)
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
    LOG.setLevel(logging.INFO)
    LOG.info('Режим: %s; компания: %s', 'ЗАПИСЬ' if APPLY else 'ПРОВЕРКА БЕЗ ЗАПИСИ', COMPANY_ID or 'все')
    c=config();api=API(c);api.validate_fields();date.fromisoformat(c['start_date'])
    schema=api.call('crm.item.fields',{'entityTypeId':c['entity_type_id'],'useOriginalUfNames':'Y'})['result']['fields']
    for key in c['fields'].values():
        if key not in schema:raise ValueError('Отсутствует поле журнала '+key)
    path=Path(c['sync_lock_path']);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a+b') as lock:
        try:lock_file(lock)
        except BlockingIOError:
            LOG.info('Предыдущий сборщик ещё работает');return 3
        old=index_journal(journal(api,c),c)
        target,blocked,errors=prepare(api,c,old,args.company)
        new_count=sum(k not in old for k in target)
        edit_count=sum(bool(diff(old[k],v,c)) for k,v in target.items() if k in old)
        LOG.info('Журнал: новых=%s, изменений=%s, дата начала=%s',new_count,edit_count,c['start_date'])
        for msg in errors:LOG.warning(msg)
        if args.apply:
            sync_journal(api,c,old,target)
            actual=index_journal(journal(api,c),c)
            for key,row in target.items():
                if key not in actual or diff(actual[key],row,c):
                    raise RuntimeError('Журнал не подтвердил записанные данные; публикация отложена')
            target=actual
        errors+=publish(api,c,target,blocked,args.apply,args.company)
        for msg in errors:LOG.warning(msg)
        LOG.info('Завершено. Исключений: %s',len(errors))
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
