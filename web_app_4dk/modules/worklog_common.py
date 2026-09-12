"""Общий REST-клиент и последовательная запись списка. Python 3.9+, Windows/Linux."""
import functools
import json
import os
import re
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import errno
if os.name == 'nt':
    import msvcrt
else:
    import fcntl
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

MONTHS = ['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь']
_LOCAL = threading.local()
_MUTEX = threading.RLock()


def lock_file(file, unlock=False):
    """Блокировка без ожидания; занято -> BlockingIOError. Файл открыт a+b."""
    if os.name != 'nt':
        fcntl.flock(file, fcntl.LOCK_UN if unlock else fcntl.LOCK_EX | fcntl.LOCK_NB)
        return
    # Windows блокирует диапазон байтов с текущей позиции.
    # msvcrt допускает блокировку диапазона за концом пустого файла.
    file.seek(0)
    try:
        msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK if unlock else msvcrt.LK_NBLCK, 1)
    except OSError as exc:
        if not unlock and exc.errno in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
            raise BlockingIOError(exc.errno, 'Файл блокировки занят') from exc
        raise


def accounting_timezone(name):
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        # Для нашего периода учёта (с сентября 2026) Москва — UTC+3.
        # На Windows база IANA может отсутствовать; дополнительные пакеты не нужны.
        if name == 'Europe/Moscow':
            return timezone(timedelta(hours=3), 'Europe/Moscow')
        raise


def config():
    from copy import deepcopy
    if __package__:
        from .worklog_settings import SETTINGS, LOCK_DIRECTORY
        from .authentication import authentication
    else:
        from worklog_settings import SETTINGS, LOCK_DIRECTORY
        try:
            from authentication import authentication
        except ModuleNotFoundError as exc:
            if exc.name != 'authentication':
                raise
            from web_app_4dk.modules.authentication import authentication
    c = deepcopy(SETTINGS)
    c['webhook_url'] = authentication('Bitrix')
    if not isinstance(c['webhook_url'], str) or not c['webhook_url'].strip():
        raise ValueError("authentication('Bitrix') не вернул вебхук")
    c['webhook_url'] = c['webhook_url'].strip()
    directory = Path(LOCK_DIRECTORY).resolve()
    c['lock_path'] = str(directory / 'list.lock')
    c['sync_lock_path'] = str(directory / 'sync.lock')
    return c


def duration(value):
    if value in (None, '', False):
        return 0
    if isinstance(value, time.struct_time):
        return value.tm_hour * 3600 + value.tm_min * 60 + value.tm_sec
    if isinstance(value, int) or str(value).isdigit():
        n = int(value)
    else:
        m = re.fullmatch(r'(\d+):([0-5]\d):([0-5]\d)', str(value))
        if not m:
            raise ValueError('Некорректная длительность: ' + str(value))
        n = int(m[1])*3600 + int(m[2])*60 + int(m[3])
    if n < 0:
        raise ValueError('Отрицательная длительность')
    return n


def hms(seconds):
    n = int(seconds)
    sign = '-' if n < 0 else ''
    h, tail = divmod(abs(n), 3600)
    m, s = divmod(tail, 60)
    return f'{sign}{h:02d}:{m:02d}:{s:02d}'


def values(value):
    if value is None or value == '' or value is False:
        return []
    if isinstance(value, dict):
        return list(value.values())
    return value if isinstance(value, list) else [value]


def scalar(row, key, default=''):
    v = values(row.get(key))
    if len(v) > 1:
        raise ValueError('Ожидалось одно значение ' + key)
    return v[0] if v else default


def month_name(period):
    year, month = map(int, period.split('-'))
    return f'{MONTHS[month-1]} {year}'


def current_period(c):
    return datetime.now(accounting_timezone(c['timezone'])).strftime('%Y-%m')


@contextmanager
def list_lock():
    # Межпроцессная блокировка + RLock для потоков Flask. Повторный вход допустим.
    with _MUTEX:
        if getattr(_LOCAL, 'depth', 0):
            _LOCAL.depth += 1
            try:
                yield
            finally:
                _LOCAL.depth -= 1
            return
        p = Path(config()['lock_path'])
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('a+b') as f:
            deadline = time.monotonic() + 60
            while True:
                try:
                    lock_file(f)
                    break
                except BlockingIOError:
                    if time.monotonic() > deadline:
                        raise RuntimeError('Не удалось получить блокировку списка за 60 секунд')
                    time.sleep(.1)
            _LOCAL.depth = 1
            try:
                yield
            finally:
                _LOCAL.depth = 0
                lock_file(f, unlock=True)


def serialized(fn):
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        with list_lock():
            return fn(*args, **kwargs)
    return wrapped


class API:
    def __init__(self, c):
        self.c = c
        self.schema = None
        self.last_call = 0
        if not c['webhook_url'].startswith('https://') or 'REPLACE' in c['webhook_url']:
            raise ValueError("authentication('Bitrix') должен возвращать реальный HTTPS вебхук")

    def call(self, method, params, write=False):
        # Записи не повторяем автоматически: при тайм-ауте результат неизвестен.
        for attempt in range(1 if write else 5):
            pause = .55 - (time.monotonic() - self.last_call)
            if pause > 0:
                time.sleep(pause)
            self.last_call = time.monotonic()
            req = Request(self.c['webhook_url'].rstrip('/')+'/'+method+'.json',
                          data=json.dumps(params).encode('utf-8'),
                          headers={'Content-Type':'application/json'}, method='POST')
            try:
                with urlopen(req, timeout=45) as response:
                    status, body = response.status, response.read()
            except HTTPError as exc:
                status, body = exc.code, exc.read()
            except (URLError, OSError):
                if not write and attempt < 4:
                    time.sleep(2**attempt)
                    continue
                raise RuntimeError(method + ': ошибка сети; результат записи может быть неизвестен') from None
            try:
                data = json.loads(body)
            except ValueError:
                data = {}
            if not isinstance(data, dict):
                data = {}
            transient = status in (429, 500, 502, 503, 504) or data.get('error') in (
                'QUERY_LIMIT_EXCEEDED', 'OPERATION_TIME_LIMIT', 'INTERNAL_SERVER_ERROR')
            if transient and not write and attempt < 4:
                time.sleep(2**attempt)
                continue
            if not 200 <= status < 300 or 'error' in data or 'result' not in data:
                raise RuntimeError(f'{method}: HTTP {status}; code={data.get("error", "bad_response")}')
            if write and not data['result']:
                raise RuntimeError(method + ': запись не подтверждена')
            return data
        raise RuntimeError(method + ': попытки исчерпаны')

    def pages(self, method, params, nested=None):
        result, start, seen = [], 0, set()
        while True:
            p = dict(params, start=start)
            reply = self.call(method, p)
            rows = reply['result']
            if nested:
                rows = rows[nested]
            if not isinstance(rows, list):
                raise RuntimeError(method + ': ожидался массив')
            result.extend(rows)
            nxt = reply.get('next')
            if nxt is None:
                break
            if int(nxt) in seen or int(nxt) <= start:
                raise RuntimeError(method + ': повтор страницы')
            seen.add(int(nxt))
            start = int(nxt)
        return result

    def list_params(self):
        return {'IBLOCK_TYPE_ID':'lists', 'IBLOCK_ID':self.c['list_id']}

    def fields(self):
        if self.schema is None:
            raw = self.call('lists.field.get', self.list_params())['result']
            rows = raw.values() if isinstance(raw, dict) else raw
            self.schema = {r['FIELD_ID']:r for r in rows}
        return self.schema

    def validate_fields(self):
        schema = self.fields()
        wanted = [self.c['tasks_field'], self.c['total_field'], self.c['total_seconds_field']]
        if len(set(wanted)) != 3 or any(k in ('PROPERTY_1303','PROPERTY_1307','PROPERTY_1299') for k in wanted):
            raise ValueError('Новые поля должны иметь три отдельных ID')
        for key, typ in zip(wanted, ('S','S','N')):
            if key not in schema:
                raise ValueError('В списке нет поля '+key)
            meta = schema[key]
            if meta.get('MULTIPLE') == 'Y' or meta.get('PROPERTY_TYPE', meta.get('TYPE')) != typ:
                raise ValueError(f'{key}: нужен одиночный тип {typ}')

    def get_element(self, element_id):
        rows = self.call('lists.element.get', dict(self.list_params(), ELEMENT_ID=str(element_id)))['result']
        if not isinstance(rows, list) or len(rows) != 1:
            raise ValueError('Не найден единственный элемент '+str(element_id))
        return rows[0]

    def find_element(self, company, period):
        rows = self.pages('lists.element.get', dict(self.list_params(), FILTER={
            'PROPERTY_1299':str(company), 'NAME':month_name(period)}))
        if len(rows) > 1:
            raise ValueError(f'Дубли месячных элементов: компания {company}, {period}')
        return rows[0] if rows else None

    def preserved_fields(self, row):
        out = {'NAME':row['NAME']}
        for key, meta in self.fields().items():
            if key == 'NAME':
                continue
            v = values(row.get(key)) if key.startswith('PROPERTY_') else row.get(key)
            if key.startswith('PROPERTY_'):
                if meta.get('TYPE') == 'F' or meta.get('PROPERTY_TYPE') == 'F':
                    raise ValueError(f'{key}: поле Файл требует отдельного обработчика сохранения')
                if any(isinstance(x, (dict, list)) for x in v):
                    raise ValueError(f'{key}: сложное значение; нужна адаптация сериализации')
                out[key] = v if meta.get('MULTIPLE') == 'Y' else (v[0] if v else '')
            elif key in row:
                out[key] = v
        unknown = [k for k in row if k.startswith('PROPERTY_') and k not in self.fields()]
        if unknown:
            raise ValueError('Нет описания полей: '+','.join(unknown))
        return out

    def totals(self, row, changes):
        out = dict(changes)
        calls = duration(out.get('PROPERTY_1303', scalar(row,'PROPERTY_1303')))
        epd = duration(out.get(self.c['tasks_field'], scalar(row,self.c['tasks_field'])))
        out[self.c['tasks_field']] = hms(epd)
        out[self.c['total_field']] = hms(calls+epd)
        out[self.c['total_seconds_field']] = str(calls+epd)
        return out

    def update_element(self, row, changes):
        # Вызывается под list_lock после свежего get_element.
        self.validate_fields()
        fields = self.preserved_fields(row)
        fields.update(self.totals(row, changes))
        return self.call('lists.element.update', dict(self.list_params(),
            ELEMENT_ID=row['ID'], FIELDS=fields), write=True)['result']


def effective_seconds(row, c):
    value = scalar(row, c['total_seconds_field'])
    if value not in ('', None):
        from decimal import Decimal
        number = Decimal(str(value))
        if not number.is_finite() or number < 0 or number != number.to_integral_value():
            raise ValueError('Некорректный общий расход в секундах')
        return int(number)
    return duration(scalar(row, 'PROPERTY_1303'))


def period_of(row):
    words = row['NAME'].strip().split()
    if len(words) != 2 or words[0] not in MONTHS or not words[1].isdigit():
        raise ValueError('Не распознано название месяца: '+str(row.get('ID')))
    return f'{int(words[1]):04d}-{MONTHS.index(words[0])+1:02d}'
