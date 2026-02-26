from datetime import datetime, timedelta
from time import sleep
import base64
import requests
from fast_bitrix24 import Bitrix
from web_app_4dk.modules.authentication import authentication

b = Bitrix(authentication('Bitrix'))

def resolve_task_division(task, group_division):
    """
    Возвращает division если задача подходит, иначе None.
    """

    try:
        group_id = int(task.get("groupId")) # достаем айди группы из задачи
    except (TypeError, ValueError):
        return None

    division = group_division.get(group_id) # достаем соответствующий айди из подразделения в списаниях
    if not division:
        return None

    tags = [t.lower() for t in (task.get("tags") or [])] # преобразует теги к одному регистру

    forbidden_tags = {
        1: {"платно"}, # теги исключаемые из затрат тлп
        321: {"платно"}, # теги исключаемые из затрат по работам итс
    }

    if group_id in forbidden_tags: # смотрим есть ли по группе исключаемые теги
        if any(tag in forbidden_tags[group_id] for tag in tags):
            return None

    if group_id == 7: # если группа = ЛК, то проверяем заполненность поля "айди обращения из коннекта"
        auto_field = task.get("ufAuto499889542776")
        if not auto_field or not str(auto_field).strip():
            return None

    return division

def get_last_processed_id(b):
    """
    Получает ID последней обработанной трудозатраты из УС 'Хранилище по лимитам тарифов' (id УС = 380, элемент 1831492).
    """

    response = b.get_all(
        "lists.element.get",
        {
            "IBLOCK_TYPE_ID": "lists",
            "IBLOCK_ID": "380",
            "ELEMENT_ID": "1831492",
        },
    )

    result = response.get("result", [])
    if not result:
        return None

    value = result[0].get("PROPERTY_2102", {}).get("VALUE")

    if not value:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None

def update_last_processed_id(b, max_id):
    """
    Обновляет last_id после успешной обработки.
    """

    b.call(
        "lists.element.update",
        {
            "IBLOCK_TYPE_ID": "lists",
            "IBLOCK_ID": "380",
            "ELEMENT_ID": "1831492",
            "FIELDS": {
                "PROPERTY_2102": max_id
            },
        },
    )

def get_active_user_ids(b):
    """
    Возвращает список ID активных пользователей ЦС, исключая пользователя 91.
    
    departments = [458, 5, 27, 29, 231]  # ГР, ЦС, ГО3, ГО4, ЛК
    all_users = []
    start = 0

    while True:
        resp = b.get_all(
            "user.get",
            {
                "filter": {"ACTIVE": True, "UF_DEPARTMENT": departments,},
                "start": start,
            },
        )

        users = resp.get("result", [])
        if not users:
            break

        all_users.extend(users)

        if "next" not in resp:
            break

        start = resp["next"]

    user_ids = []
    for u in all_users:
        uid = int(u["ID"])
        if uid != 91: # исключаем дежурного админа
            user_ids.append(uid)

    return user_ids
    """
    user_ids = 1391
    return user_ids

def get_new_elapsed_items(b, user_ids, last_id=None):
    """
    Возвращает список новых трудозатрат.
    """

    if last_id: # есть есть айди последней обработанной трудозатраты, то фильтруем по айди
        filter_block = {
            ">ID": last_id,
            "USER_ID": user_ids,
        }
    else: # есть нет айди последней обработанной трудозатраты, то фильтруем за последние два часа
        two_hours_ago = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S")
        filter_block = {
            ">=CREATED_DATE": two_hours_ago,
            "USER_ID": user_ids,
        }

    items = []
    page = 1

    while True:
        resp = b.call(
            "task.elapseditem.getlist",
            {
                "order": {"ID": "asc"},
                "filter": filter_block,
                "select": ["*"],
                "params": {
                    "NAV_PARAMS": {
                        "nPageSize": 50,
                        "iNumPage": page,
                    }
                },
            },
            raw=True,
        )

        result = resp.get("result", [])
        if not result:
            break

        items.extend(result)
        page += 1

        if page > 100: # ограничение по кол-ву забираемых трудозатрат в 5000 штук
            print("Превышен лимит страниц")
            break

    return items    

def process_elapsed_item(b, item, group_division):
    """
    Обрабатывает одну трудозатрату. Возвращает True если создана/обновлена запись.
    """

    seconds = int(item.get("SECONDS", 0)) # забираем время из трудозатраты, если оно есть
    if seconds <= 0:
        return False

    task_id = item.get("TASK_ID") # id задачи из трудозатраты
    if not task_id:
        return False

    task_resp = b.get_all(  # получаем задачу
        "tasks.task.get",
        {
            "taskId": task_id,
            "select": [
                "ID",
                "GROUP_ID",
                "UF_CRM_TASK",
                "TAGS",
                "UF_AUTO_499889542776", # id обращения из коннекта
            ],
        },
    )

    task = task_resp.get("result", {}).get("task")
    if not task:
        return False

    division = resolve_task_division(task, group_division) # выясненяем подходящее подразделение в списании
    if not division:
        return False

    uf_crm = task.get("ufCrmTask", []) # достаем привязанные crm сущности из задачи
    if not uf_crm:
        return False

    company_id = None
    contact_id = None

    for link in uf_crm:
        if link.startswith("CO_"):
            company_id = int(link.replace("CO_", ""))
        elif link.startswith("C_"):
            contact_id = int(link.replace("C_", ""))

    if not company_id: # если в задаче нет компании, то пропускаем эту трудозатрату
        return False

    existing = b.get_all( # проверяем дубли трудозатрат по айди
        "crm.item.list",
        {
            "entityTypeId": 1118,
            "filter": {"UF_CRM_96_ID_ELAPSEDTIME": item["ID"]},
            "select": ["id", "UF_CRM_96_TIMECOST_SECONDS"],
        },
    )
    existing_items = existing.get("result", {}).get("items", [])

    # Конвертация времени
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    time_str = f"{hours:02}:{minutes:02}:{secs:02}"

    if existing_items: # если на трудозатрату уже создано списание, то обновляем время трудозатраты при изменениях
        existing_item = existing_items[0]
        existing_seconds = int(existing_item.get("UF_CRM_96_TIMECOST_SECONDS", 0))

        if existing_seconds != seconds:
            b.call(
                "crm.item.update",
                {
                    "entityTypeId": 1118,
                    "id": existing_item["id"],
                    "fields": {
                        "UF_CRM_96_TIME_COST": time_str,
                        "UF_CRM_96_TIMECOST_SECONDS": seconds,
                    },
                },
            )
            return True

        return False

    
    b.call( # создаем новое списание
        "crm.item.add",
        {
            "entityTypeId": 1118,
            "fields": {
                "UF_CRM_96_RESPONSIBLE": item["USER_ID"],
                "UF_CRM_96_DATE_COMPLETE": item["CREATED_DATE"],
                "UF_CRM_96_TIME_COST": time_str,
                "UF_CRM_96_DIVISION": division,
                "UF_CRM_96_ID_TASK": task["id"],
                "UF_CRM_96_TIMECOST_SECONDS": seconds,
                "UF_CRM_96_COMPANY": company_id,
                "UF_CRM_96_CONTACT": contact_id,
                "UF_CRM_96_ID_ELAPSEDTIME": item["ID"],
            },
        },
    )

    return True

def sync_elapsed_items(b):

    group_division = { # соответствие айди группы задачи и айди подразделения в списании
        1: 2236,
        7: 2234,
        321: 2248,
    }

    last_id = get_last_processed_id(b) # достаем айди последней обработанной трудозатраты
    user_ids = get_active_user_ids(b) # достаем список активных сотрудников ЦС

    if not user_ids:
        print("Нет активных пользователей")
        return

    elapsed_items = get_new_elapsed_items(b, user_ids, last_id) # возвращаем список новых трудозатрат

    if not elapsed_items:
        print("Новых трудозатрат нет")
        return

    processed = []

    for item in elapsed_items:
        if process_elapsed_item(b, item, group_division):
            processed.append(item)

    # Обновляем last_id по любому последнему элементу
    max_id = max(int(i["ID"]) for i in elapsed_items)
    update_last_processed_id(b, max_id)
    print(f"Синхронизация завершена. Новый last_id = {max_id}")

    if not processed:
        print("Подходящих трудозатрат не найдено")

if __name__ == '__main__':

    sync_elapsed_items()
