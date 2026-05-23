# jobs/sync_connect_contact.py
"""
Автоматическая привязка контакта Битрикс24 к пользователю 1С:Коннект.

Что делает job:
1. Получает контакт Битрикс24 по contact_id.
2. Ищет пользователя в 1С:Коннект по email и ФИО.
3. Через SOAP получает компанию пользователя в 1С:Коннект и ИНН компании.
4. Находит компанию Битрикс24 по ИНН.
5. Обновляет поля контакта:
   - UF_CRM_1666098408 — "Есть в коннекте"
   - UF_CRM_1666338025722 — "1С Коннект ID"
6. Делает upsert в SQLite-таблицу companies:
   - author_id   = ID пользователя в 1С:Коннект
   - connect_id  = ID компании в 1С:Коннект
   - bitrix_id   = ID компании в Битрикс24
   - author_name = имя контакта для логов

Ожидаемый вызов из робота:
{{Константы глобальные: IP веб-приложения}}/bitrix/custom_webhook?job=sync_connect_contact&contact_id={{ID}}

Важно:
- Не храните логин/пароль 1С:Коннект в коде. Передайте их через переменные окружения:
  CONNECT_API_USER
  CONNECT_API_PASSWORD
- Если поле UF_CRM_1666098408 является списком, в BITRIX_CONNECT_YES_VALUE нужно указать ID значения "да",
  а не текст "да".
"""

from __future__ import annotations

import os
import re
import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

import requests
from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client
from zeep.transports import Transport

try:
    from authentication import authentication
except ModuleNotFoundError:
    from web_app_4dk.modules.authentication import authentication


DEFAULT_DB = os.getenv("CONNECT_DB", "/root/web_app_4dk/web_app_4dk/modules/1C_Connect.db")

CONNECT_SUBSCRIBERS_URL = os.getenv(
    "CONNECT_SUBSCRIBERS_URL",
    "https://push.1c-connect.com/v1/line/subscribers/",
)

CONNECT_WSDL_URL = os.getenv(
    "CONNECT_WSDL_URL",
    "https://cus.buhphone.com/cus/ws/PartnerWebAPI2?wsdl",
)

CONNECT_API_USER = authentication("ConnectLogin")
CONNECT_API_PASSWORD = authentication("ConnectPassword")

# Для поля "Есть в коннекте".
# Если в Битрикс24 это поле типа "список", сюда надо положить ID варианта "да".
CONTACT_IN_CONNECT_FIELD = "UF_CRM_1666098408"
CONTACT_IN_CONNECT_VALUE = os.getenv("BITRIX_CONNECT_YES_VALUE", "Y")

CONTACT_CONNECT_ID_FIELD = "UF_CRM_1666338025722"
COMPANY_INN_FIELD = "UF_CRM_1656070716"

DEFAULT_NOTIFY_USER_ID = "1"


UPSERT_SQL = """
INSERT INTO companies(author_id, connect_id, bitrix_id, author_name)
VALUES (?, ?, ?, ?)
ON CONFLICT(author_id) DO UPDATE SET
  connect_id=excluded.connect_id,
  bitrix_id=excluded.bitrix_id,
  author_name=excluded.author_name;
"""


@dataclass
class ConnectUser:
    user_id: str
    name: str
    raw: Dict[str, Any]
    score: int


@dataclass
class ConnectCompanyInfo:
    company_id: str
    inn: str
    author_name: str


def _bitrix(method: str, data: Optional[dict] = None) -> Any:
    """Вызов REST Битрикс24 через ваш authentication('Bitrix')."""
    response = requests.post(f"{authentication('Bitrix')}{method}", json=data or {}, timeout=60)
    payload = response.json()
    if "error" in payload:
        raise RuntimeError(f"Bitrix API error {method}: {payload.get('error_description') or payload.get('error')}")
    return payload.get("result")


def _notify(user_id: str, message: str) -> None:
    """
    Пытаемся отправить системное уведомление.
    Если метод недоступен на портале, создаем задачу как запасной вариант.
    """
    try:
        _bitrix("im.notify.system.add", {
            "USER_ID": user_id,
            "MESSAGE": message,
        })
    except Exception:
        _bitrix("tasks.task.add", {
            "fields": {
                "TITLE": "1С:Коннект: проблема с привязкой контакта",
                "DESCRIPTION": message,
                "CREATED_BY": user_id,
                "RESPONSIBLE_ID": user_id,
            }
        })


def _normalize_text(value: Any) -> str:
    value = str(value or "").lower().replace("ё", "е")
    value = re.sub(r"[^a-zа-я0-9@._+\-\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _contact_emails(contact: Mapping[str, Any]) -> List[str]:
    emails = []
    for item in contact.get("EMAIL") or []:
        if isinstance(item, dict) and item.get("VALUE"):
            emails.append(str(item["VALUE"]).strip().lower())
        elif isinstance(item, str):
            emails.append(item.strip().lower())
    return [x for x in emails if x]


def _contact_full_name(contact: Mapping[str, Any]) -> str:
    parts = [
        contact.get("LAST_NAME"),
        contact.get("NAME"),
        contact.get("SECOND_NAME"),
    ]
    return " ".join(str(x).strip() for x in parts if x).strip()


def _iter_scalar_values(obj: Any) -> Iterable[str]:
    if isinstance(obj, dict):
        for value in obj.values():
            yield from _iter_scalar_values(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _iter_scalar_values(value)
    elif obj is not None:
        yield str(obj)


def _field_by_possible_names(row: Mapping[str, Any], names: Iterable[str]) -> str:
    names_lower = {n.lower() for n in names}
    for key, value in row.items():
        if str(key).lower() in names_lower and value is not None:
            return str(value).strip()
    return ""


def _candidate_id(row: Mapping[str, Any]) -> str:
    if row.get("user_id"):
        return str(row["user_id"]).strip()

    direct = _field_by_possible_names(row, [
        "id", "user_id", "userid", "userId", "connect_id", "author_id", "client_user_id", "ClientUserID"
    ])
    if direct:
        return direct

    for value in _iter_scalar_values(row):
        value = value.strip()
        if re.fullmatch(r"[0-9a-fA-F\-]{8,}", value) or re.fullmatch(r"\d{3,}", value):
            return value

    return ""


def _candidate_email_blob(row: Mapping[str, Any]) -> str:
    if row.get("email"):
        return str(row["email"]).strip().lower()

    direct = _field_by_possible_names(row, [
        "email", "e_mail", "mail", "Email", "EMail", "login", "Login"
    ])
    if direct:
        return direct.lower()

    values = " ".join(_iter_scalar_values(row)).lower()
    found = re.findall(r"[\w.+\-]+@[\w\-]+\.[\w.\-]+", values)
    return " ".join(found)


def _candidate_name(row: Mapping[str, Any]) -> str:
    surname = str(row.get("surname") or "").strip()
    name = str(row.get("name") or "").strip()
    patronymic = str(row.get("patronymic") or "").strip()

    full_name = " ".join(x for x in [surname, name, patronymic] if x).strip()
    if full_name:
        return full_name

    direct = _field_by_possible_names(row, [
        "full_name", "fullName", "display_name", "displayName", "fio", "title", "Name"
    ])
    if direct:
        return direct

    return " ".join(_iter_scalar_values(row))


def _score_subscriber(row: Mapping[str, Any], emails: List[str], full_name: str) -> Tuple[int, str]:
    email_blob = _candidate_email_blob(row)
    candidate_name = _normalize_text(_candidate_name(row))

    score = 0

    for email in emails:
        if email and email in email_blob:
            score += 100

    contact_tokens = [t for t in _normalize_text(full_name).split() if len(t) >= 2]
    if contact_tokens:
        matched = sum(1 for token in contact_tokens if token in candidate_name)
        if matched == len(contact_tokens):
            score += 60
        elif matched >= 2:
            score += 35
        elif matched == 1:
            score += 10

    return score, candidate_name


def _fetch_subscribers() -> List[Dict[str, Any]]:
    if not CONNECT_API_USER or not CONNECT_API_PASSWORD:
        raise RuntimeError(
            "Не заданы переменные окружения CONNECT_API_USER и CONNECT_API_PASSWORD "
            "для доступа к REST API 1С:Коннект."
        )

    response = requests.get(
        CONNECT_SUBSCRIBERS_URL,
        auth=(CONNECT_API_USER, CONNECT_API_PASSWORD),
        headers={"accept": "application/json"},
        timeout=90,
    )
    response.raise_for_status()
    data = response.json()

    if not isinstance(data, list):
        raise RuntimeError(f"Ожидался список подписчиков 1С:Коннект, получен тип: {type(data).__name__}")

    return [x for x in data if isinstance(x, dict)]


def _find_connect_user(contact: Mapping[str, Any]) -> Optional[ConnectUser]:
    emails = _contact_emails(contact)
    full_name = _contact_full_name(contact)

    if not emails and not full_name:
        return None

    best: Optional[ConnectUser] = None
    for row in _fetch_subscribers():
        score, candidate_name = _score_subscriber(row, emails, full_name)
        user_id = _candidate_id(row)
        if not user_id:
            continue

        if best is None or score > best.score:
            best = ConnectUser(
                user_id=user_id,
                name=candidate_name or full_name,
                raw=row,
                score=score,
            )

    # 100 = уверенное совпадение по email, 60 = полное совпадение по ФИО.
    # Ниже 60 лучше считать сомнительным и отдать человеку на проверку.
    if best and best.score >= 60:
        return best

    return None


def _connect_soap_client() -> Client:
    if not CONNECT_API_USER or not CONNECT_API_PASSWORD:
        raise RuntimeError(
            "Не заданы переменные окружения CONNECT_API_USER и CONNECT_API_PASSWORD "
            "для доступа к SOAP API 1С:Коннект."
        )

    session = Session()
    session.auth = HTTPBasicAuth(CONNECT_API_USER, CONNECT_API_PASSWORD)
    return Client(CONNECT_WSDL_URL, transport=Transport(session=session))


def _get_connect_company_info(author_id: str) -> Optional[ConnectCompanyInfo]:
    """
    Логика повторяет существующий get_connect_company_id:
    ClientUserRead дает связь пользователь -> компания,
    ClientRead дает реквизиты компании, включая ИНН.
    """
    xml_client = _connect_soap_client()

    employees = xml_client.service.ClientUserRead("Params")
    companies = xml_client.service.ClientRead("Params")

    employees_rows = employees[1]["Value"]["row"]
    companies_rows = companies[1]["Value"]["row"]

    for employee in employees_rows:
        values = employee["Value"]
        if str(values[0]) != str(author_id):
            continue

        employee_company_id = str(values[1])
        author_name = f"{values[4]} {values[5]}".strip()

        for company in companies_rows:
            c_values = company["Value"]
            if str(c_values[0]) == employee_company_id and c_values[4]:
                return ConnectCompanyInfo(
                    company_id=str(c_values[0]),
                    inn=str(c_values[4]).strip(),
                    author_name=author_name,
                )

    return None


def _find_bitrix_company_by_inn(inn: str) -> Optional[str]:
    result = _bitrix("crm.company.list", {
        "select": ["ID", COMPANY_INN_FIELD],
        "filter": {
            COMPANY_INN_FIELD: inn,
        }
    })
    if result:
        return str(result[0]["ID"])
    return None


def _update_bitrix_contact(contact_id: str, connect_user_id: str) -> None:
    _bitrix("crm.contact.update", {
        "id": contact_id,
        "fields": {
            CONTACT_IN_CONNECT_FIELD: CONTACT_IN_CONNECT_VALUE,
            CONTACT_CONNECT_ID_FIELD: connect_user_id,
        }
    })


def _exec_upsert(db_path: str, author_id: str, connect_id: str, bitrix_id: str, author_name: str) -> None:
    con = sqlite3.connect(db_path, timeout=5, isolation_level=None)
    try:
        con.execute("PRAGMA busy_timeout=3000")
        try:
            con.execute("BEGIN IMMEDIATE")
            con.execute(UPSERT_SQL, (author_id, connect_id, bitrix_id, author_name))
            con.commit()
        except sqlite3.OperationalError:
            # Фолбэк на случай старого SQLite или отсутствия UNIQUE(author_id).
            con.rollback()
            con.execute("BEGIN IMMEDIATE")
            cur = con.execute(
                "UPDATE companies SET connect_id=?, bitrix_id=?, author_name=? WHERE author_id=?",
                (connect_id, bitrix_id, author_name, author_id),
            )
            if cur.rowcount == 0:
                con.execute(
                    "INSERT INTO companies(author_id, connect_id, bitrix_id, author_name) VALUES (?, ?, ?, ?)",
                    (author_id, connect_id, bitrix_id, author_name),
                )
            con.commit()
    finally:
        con.close()


def sync_connect_contact_job(params: Mapping[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """
    Главная функция для custom_webhook.

    Параметры:
    - contact_id / bitrix_contact_id / id — ID контакта Битрикс24
    - notify_user_id — кому отправлять сообщение об ошибке, по умолчанию 1
    - db — путь к SQLite, по умолчанию CONNECT_DB или стандартный путь проекта
    """
    contact_id = str(
        params.get("contact_id")
        or params.get("bitrix_contact_id")
        or params.get("id")
        or ""
    ).strip()

    notify_user_id = str(params.get("notify_user_id") or DEFAULT_NOTIFY_USER_ID).strip()
    db_path = str(params.get("db") or DEFAULT_DB).strip()

    if not contact_id:
        return 400, {"ok": False, "error": "missing param: contact_id"}

    try:
        contact = _bitrix("crm.contact.get", {"id": contact_id})
        if not contact:
            message = f"Возникли проблемы с поиском контакта: контакт Битрикс24 ID {contact_id} не найден."
            _notify(notify_user_id, message)
            return 404, {"ok": False, "error": message}

        contact_name = _contact_full_name(contact) or f"Контакт Б24 #{contact_id}"
        emails = _contact_emails(contact)

        connect_user = _find_connect_user(contact)
        if not connect_user:
            message = (
                "Возникли проблемы с поиском контакта в 1С:Коннект.\n\n"
                f"Контакт Битрикс24: {contact_name} (ID {contact_id})\n"
                f"Email: {', '.join(emails) if emails else 'не указан'}\n\n"
                "Автоматическое совпадение по email/ФИО не найдено или недостаточно надежно."
            )
            _notify(notify_user_id, message)
            return 422, {"ok": False, "error": "connect user not found", "message": message}

        company_info = _get_connect_company_info(connect_user.user_id)
        if not company_info:
            message = (
                "Возникли проблемы с поиском компании контакта в 1С:Коннект.\n\n"
                f"Контакт Битрикс24: {contact_name} (ID {contact_id})\n"
                f"ID пользователя 1С:Коннект: {connect_user.user_id}"
            )
            _notify(notify_user_id, message)
            return 422, {"ok": False, "error": "connect company not found", "message": message}

        bitrix_company_id = _find_bitrix_company_by_inn(company_info.inn)
        if not bitrix_company_id:
            message = (
                "Возникли проблемы с поиском компании в Битрикс24 по ИНН.\n\n"
                f"Контакт Битрикс24: {contact_name} (ID {contact_id})\n"
                f"ID пользователя 1С:Коннект: {connect_user.user_id}\n"
                f"ID компании 1С:Коннект: {company_info.company_id}\n"
                f"ИНН: {company_info.inn}"
            )
            _notify(notify_user_id, message)
            return 422, {"ok": False, "error": "bitrix company not found", "message": message}

        _update_bitrix_contact(contact_id, connect_user.user_id)

        # Имя для логов лучше брать из Битрикс24, как вы и предложили.
        author_name = contact_name or company_info.author_name or connect_user.name

        _exec_upsert(
            db_path=db_path,
            author_id=connect_user.user_id,
            connect_id=company_info.company_id,
            bitrix_id=bitrix_company_id,
            author_name=author_name,
        )

        return 200, {
            "ok": True,
            "contact_id": contact_id,
            "contact_name": contact_name,
            "connect_user_id": connect_user.user_id,
            "connect_company_id": company_info.company_id,
            "company_inn": company_info.inn,
            "bitrix_company_id": bitrix_company_id,
            "match_score": connect_user.score,
        }

    except Exception as e:
        message = (
            "Возникла техническая ошибка при автоматической привязке контакта 1С:Коннект.\n\n"
            f"Контакт Битрикс24 ID: {contact_id}\n"
            f"Ошибка: {e}"
        )
        try:
            _notify(notify_user_id, message)
        except Exception:
            pass
        return 500, {"ok": False, "error": str(e)}
