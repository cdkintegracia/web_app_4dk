from datetime import datetime, timedelta
from time import sleep
import base64
import requests
from fast_bitrix24 import Bitrix
from web_app_4dk.modules.authentication import authentication

b = Bitrix(authentication('Bitrix'))

def calls_lk_limit():

    users = b.get_all( # все сотрудники ЛК
        'user.get',
        {'filter': {'ACTIVE': True, 'UF_DEPARTMENT': 231}, 'select': ['ID']}
    )

    user_ids_lk = []
    for u in users:
        uid = int(u['ID'])
        if uid != 19 and uid != 117: # исключаем СЮВ и РЕВ
            user_ids_lk.append(uid)

    date_from = (datetime.now() - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S") # последние 5 часов для того, чтобы учесть длительные звонки

    calls = b.get_all(
        'voximplant.statistic.get',
        {
            'filter': {
                'CALL_TYPE': 1,
                'PORTAL_USER_ID': user_ids_lk,
                '>CALL_START_DATE': date_from,
                'CALL_FAILED_CODE': '200',
            }
        }
    )
    #print("Найдено звонков:", len(calls))

    # сначала собираем все компании из звонков
    call_companies = {}
    all_company_ids = set()

    for item in calls:

        crm_id = item.get("CRM_ENTITY_ID")
        crm_type = item.get("CRM_ENTITY_TYPE")

        if not crm_id:
            continue

        contact_id = None
        company_ids = []

        if crm_type == "CONTACT":

            contact_id = crm_id

            companies = b.get_all('crm.contact.company.items.get', {'id': contact_id})

            if companies:
                for c in companies:
                    cid = c.get("COMPANY_ID")
                    if cid:
                        cid = int(cid)
                        company_ids.append(cid)
                        all_company_ids.add(cid)

        elif crm_type == "COMPANY":
            cid = int(crm_id)
            company_ids = [cid]
            all_company_ids.add(cid)

        call_companies[item["ID"]] = {
            "company_ids": company_ids,
            "contact_id": contact_id
        }


    # получаем все компании сразу
    companies = b.get_all(
        'crm.company.list',
        {
            'filter': {'ID': list(all_company_ids)},
            'select': ['ID', 'UF_CRM_1770898836']
        }
    )

    company_limits = {
        int(c["ID"]): c.get("UF_CRM_1770898836")
        for c in companies
        if c.get("UF_CRM_1770898836")
    }

    limit_ids = list(set(company_limits.values()))


    # получаем все лимиты сразу
    limits = b.get_all(
        'crm.item.list',
        {
            'entityTypeId': 1114,
            'filter': {'id': limit_ids},
            'select': ['id', 'stageId']
        }
    )

    valid_limits = {
        int(l['id'])
        for l in limits
        if l.get('stageId') == "DT1114_128:2"
    }


    # основной цикл обработки звонков
    for item in calls:

        data = call_companies.get(item["ID"])

        if not data:
            continue

        contact_id = data["contact_id"]
        company_ids = data["company_ids"]

        for company_id in company_ids:

            limit_id = company_limits.get(company_id)

            if not limit_id or int(limit_id) not in valid_limits:
                continue

            existing = b.get_all( # проверяем дубли трудозатрат по айди в списаниях
                'crm.item.list',
                {
                    'entityTypeId': 1118,
                    'filter': {
                        'ufCrm96_IdElapsedtime': item['ID'],
                        'ufCrm96_Division': 2234
                    },
                },
            )

            if existing:
                continue

            # Конвертация времени
            duration = int(item['CALL_DURATION']) # длительность в сек
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            secs = duration % 60
            time_str = f"{hours:02}:{minutes:02}:{secs:02}"

            b.call(
                'crm.item.add',
                {
                    'entityTypeId': 1118,
                    'fields': {
                        'ufCrm96_Responsible': item['PORTAL_USER_ID'],
                        'ufCrm96_DateComplete': item['CALL_START_DATE'],
                        'ufCrm96_TimeCost': time_str,
                        'ufCrm96_Division': 2234,
                        'ufCrm96_TimecostSeconds': duration,
                        'ufCrm96_Company': company_id,
                        'ufCrm96_Contact': contact_id,
                        'parentId1114': limit_id,
                        'ufCrm96_IdElapsedtime': item['ID'],
                    },
                },
                raw=True,
            )

def resolve_task_division(task, group_division):
    """
    Возвращает Id подразделения в списании если задача подходит, иначе None.
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

def get_active_user_ids():
    """
    Возвращает список ID активных пользователей ЦС, исключая пользователя 91.
    """
    departments = [458, 5, 27, 29, 231]  # ГР, ЦС, ГО3, ГО4, ЛК

    users_cs = b.get_all(
        'user.get',
        {'filter': {'ACTIVE': True, 'UF_DEPARTMENT': departments}, 'select': ['ID']},
    )

    user_ids = []
    for u in users_cs:
        uid = int(u['ID'])
        if uid != 91: # исключаем дежурного админа
            user_ids.append(uid)
    
    #user_ids = 1391
    return user_ids

def get_new_elapsed_items(user_ids, last_id=None):
    """
    Возвращает список всех новых трудозатрат ЦС.
    """

    if last_id: # есть есть айди последней обработанной трудозатраты, то фильтруем по айди
        filter_block = {
            ">ID": last_id,
            "USER_ID": user_ids,
        }

    else: # есть нет айди последней обработанной трудозатраты, то фильтруем за последние 3 часа и 15 минут
        two_hours_ago = (datetime.now() - timedelta(hours=3, minutes=15)).strftime("%Y-%m-%dT%H:%M:%S")
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
            notification_users = ['1391'] #, '1']
            for user in notification_users:
                b.call('im.notify.system.add', {
                                    'USER_ID': user,
                                    'MESSAGE': f'Кол-во трудозатрат превысило 5000 шт за один раз. \n[b]Выгрузка по процессу Лимиты тарифов (LimitTariff)[/b]'})
            break

    return items    

def process_elapsed_item(item, group_division):
    """
    Обрабатывает одну трудозатрату. Возвращает True если создана/обновлена запись.
    """

    seconds = int(item.get("SECONDS", 0)) # забираем время из трудозатраты, если оно есть
    if seconds <= 0:
        #print(f"Не указано время {item['ID']}")
        return False

    task_id = item.get("TASK_ID") # id задачи из трудозатраты
    if not task_id:
        #print(f"Нет айди задачи {item['ID']}")
        return False

    try:
        task = b.get_all(  # получаем задачу
            'tasks.task.get',
            {
                'taskId': task_id,
                'select': [
                    'ID',
                    'GROUP_ID',
                    'UF_CRM_TASK',
                    'TAGS',
                    'UF_AUTO_499889542776', # id обращения из коннекта
                ],
            },
        )['task']

    except:
        #print(f"Не получили задачу {item['ID']}")
        return False

    division = resolve_task_division(task, group_division) # выясненяем подходящее подразделение в списании
    if not division:
        #print(f"Не получили подразделение {item['ID']}")
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
        #print(f"В задаче нет компании {item['ID']}")
        return False
    
    try:
        company = b.get_all(
            'crm.company.get',
            {
                'id': company_id,
                'select': ['ID', 'UF_CRM_1770898836'],
            },
        )
    except:
        if not company:
            #print(f"Не смогли получить компанию {item['ID']}")
            return False

    limit_id = company.get("UF_CRM_1770898836")

    if limit_id: # если в компании указан лимит — проверяем его
        try:
            limit_item = b.get_all(
                'crm.item.get',
                {
                    'entityTypeId': 1114,
                    'id': limit_id,
                    'select': ['id', 'stageId'],
                },
            )['item']
        except:
            return False

        # если лимита нет или он не в нужной стадии — не создаем списание
        if not limit_item or limit_item.get('stageId') != "DT1114_128:2":
            #print(f"Нет подх лимита в компании {item['ID']}")
            return False

        existing = b.get_all( # проверяем дубли трудозатрат по айди в списаниях
            'crm.item.list',
            {
                'entityTypeId': '1118',
                'filter': {'ufCrm96_IdElapsedtime': item['ID']},
                'select': ['id', 'ufCrm96_Timecostseconds'],
            },
        )

        # Конвертация времени
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        time_str = f"{hours:02}:{minutes:02}:{secs:02}"

        if existing: # если на трудозатрату уже создано списание, то обновляем время трудозатраты при изменениях
            existing_item = existing[0]
            existing_seconds = int(existing_item.get('ufCrm96_Timecostseconds', 0))

            if existing_seconds != seconds:
                b.call(
                    'crm.item.update',
                    {
                        'entityTypeId': '1118',
                        'id': existing_item['id'],
                        'fields': {
                            'ufCrm96_TimeCost': time_str,
                            'ufCrm96_TimecostSeconds': seconds,
                        },
                    },
                raw=True,
                )
                return True

            return False


        b.call( # создаем новое списание, если еще не создано
            'crm.item.add',
            {
                'entityTypeId': '1118',
                'fields': {
                    'ufCrm96_Responsible': item['USER_ID'],
                    'ufCrm96_DateComplete': item['CREATED_DATE'],
                    'ufCrm96_TimeCost': time_str,
                    'ufCrm96_Division': division, 
                    'ufCrm96_IdTask': task['id'],
                    'ufCrm96_TimecostSeconds': seconds,
                    'ufCrm96_Company': company_id,
                    'ufCrm96_Contact': contact_id,
                    'parentId1114': limit_id,
                    'ufCrm96_IdElapsedtime': item['ID'],
                },
            },
        raw=True,
        )

        return True

def elapsed_times_lines(req):

    calls_lk_limit() # выгрузка звонков ЛК

    group_division = { # соответствие айди группы задачи и айди значения поля Подразделение в СП Списания
        1: 2236, # тлп
        7: 2234, # лк
        321: 2248, # работыитс
    }

    # получаем ID последней обработанной трудозатраты из УС 'Хранилище по лимитам тарифов' (id УС = 380, элемент 1831492)
    last_spent_time = b.get_all('lists.element.get', {
        'IBLOCK_TYPE_ID': 'lists',
        'IBLOCK_ID': '380',
        'ELEMENT_ID': '1831492'
    })[0]
    last_spent_time = last_spent_time.get('PROPERTY_2102')

    if last_spent_time:
        last_id = list(last_spent_time.values())[0]
    else:
        last_id = None # если нет последнего id то оставляем пустой, будем брать за последние 2 часа затраты

    user_ids = get_active_user_ids() # достаем список активных сотрудников ЦС

    if not user_ids:
        notification_users = ['1391'] #, '1']
        for user in notification_users:
            b.call('im.notify.system.add', {
                                'USER_ID': user,
                                'MESSAGE': f'Сотрудники в ЦС не найдены. \n[b]Выгрузка по процессу Лимиты тарифов (LimitTariff)[/b]'})
        return

    elapsed_items = get_new_elapsed_items(user_ids, last_id) # возвращаем список новых трудозатрат

    if not elapsed_items:
        notification_users = ['1391'] #, '1']
        for user in notification_users:
            b.call('im.notify.system.add', {
                                'USER_ID': user,
                                'MESSAGE': f'Звонки выгружены. Новых трудозатрат ЦС на портале не было. \n[b]Выгрузка по процессу Лимиты тарифов (LimitTariff)[/b]'})
        return

    processed = []
    for item in elapsed_items:
        if process_elapsed_item(item, group_division): # проверяем и обрабатываем полученные трудозатраты
            processed.append(item)

    # обновляем ID последней обработанной трудозатраты
    max_id = max(int(i["ID"]) for i in elapsed_items)
    b.call(
        "lists.element.update",
        {
            "IBLOCK_TYPE_ID": "lists",
            "IBLOCK_ID": "380",
            "ELEMENT_ID": "1831492",
            "FIELDS": {
                "NAME": 'Id последней трудозатраты',
                "PROPERTY_2102": max_id
            },
        },
        raw=True,
    )

    notification_users = ['1391'] #, '1']
    for user in notification_users:
        b.call('im.notify.system.add', {
                            'USER_ID': user,
                            'MESSAGE': f'Звонки и трудозатраты выгружены. Новый last_id = {max_id}. \n[b]Выгрузка по процессу Лимиты тарифов (LimitTariff)[/b]'})

    if not processed:
        #print("Подходящих трудозатрат не найдено")
        return
       
if __name__ == '__main__':

    elapsed_times_lines()
