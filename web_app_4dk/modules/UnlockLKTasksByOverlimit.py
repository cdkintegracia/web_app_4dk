# -*- coding: utf-8 -*-
"""
Разблокировка задач ЛК по задаче превышения лимита.

Запуск из робота в группе "Превышение лимита":
/bitrix/custom_webhook?job=unlock_lk_tasks_by_overlimit&task_id={{ID}}

Скрипт:
1. получает task_id задачи превышения;
2. проверяет, что это задача из группы "Превышение лимита";
3. проверяет, что стадия разрешающая;
4. достает компанию из штатного поля UF_CRM_TASK;
5. ищет задачи ЛК этой компании в стадии "Отложено";
6. среди них оставляет только задачи с тегом "БлокЛимита";
7. возвращает их в стадию "Новые" и пишет комментарий.
"""

from web_app_4dk.tools import send_bitrix_request


#2026-05-03 Разблокировка задач ЛК по превышению -- НАЧАЛО
GROUP_LK = '7'
GROUP_OVERLIMIT = '87'

LK_STAGE_NEW = '555'
LK_STAGE_DEFERRED = '73'

OVERLIMIT_STAGE_CONTROL = '2952'
OVERLIMIT_STAGE_PAID_SOON = '2954'
OVERLIMIT_STAGE_FORBID_LK = '2956'
OVERLIMIT_STAGE_INVOICE_SENT = '2958'
OVERLIMIT_STAGE_FORGIVEN = '1259'

# Стадии, после перехода в которые можно возвращать отложенные задачи ЛК в работу.
OVERLIMIT_UNLOCK_STAGES = {
    OVERLIMIT_STAGE_CONTROL,
    OVERLIMIT_STAGE_PAID_SOON,
    OVERLIMIT_STAGE_FORGIVEN,
    OVERLIMIT_STAGE_INVOICE_SENT,
}

TAG_LIMIT_BLOCK = 'БлокЛимита'

BITRIX_DOMAIN = 'https://vc4dk.bitrix24.ru'


def get_request_value(req, key, default=''):
    """Безопасно достаем параметр из request.args / dict."""
    try:
        value = req.get(key, default)
    except Exception:
        value = default
    return str(value).strip() if value is not None else default


def get_task_company_id(task_info):
    """
    Берем компанию из штатной CRM-привязки задачи.
    Возвращает строковый ID компании без префикса CO_.
    """
    uf_crm_task = task_info.get('ufCrmTask') or task_info.get('UF_CRM_TASK') or []

    if not uf_crm_task:
        return ''

    company_crm = list(filter(lambda x: 'CO_' in x, uf_crm_task))
    if company_crm:
        return company_crm[0][3:]

    return ''


def get_task_url(task_info):
    """Формируем ссылку на задачу."""
    task_id = task_info.get('id') or task_info.get('ID')
    group_id = task_info.get('groupId') or task_info.get('GROUP_ID')
    responsible_id = task_info.get('responsibleId') or task_info.get('RESPONSIBLE_ID')

    if group_id and str(group_id) != '0':
        return f'{BITRIX_DOMAIN}/workgroups/group/{group_id}/tasks/task/view/{task_id}/'

    return f'{BITRIX_DOMAIN}/company/personal/user/{responsible_id}/tasks/task/view/{task_id}/'


def add_task_comment(task_id, message):
    """Добавляем комментарий к задаче."""
    send_bitrix_request('task.commentitem.add', {
        'TASKID': task_id,
        'FIELDS': {
            'POST_MESSAGE': message
        }
    })


def get_task_tags(task_id):
    """Получаем теги задачи. Если получить не удалось, возвращаем пустой список."""
    tags = send_bitrix_request('task.item.gettags', {'taskId': task_id})
    if not tags:
        return []
    return tags


def remove_task_tags(task_info, tags_to_remove):
    """Удаляем служебные теги, остальные теги сохраняем."""
    task_id = task_info.get('id') or task_info.get('ID')
    current_tags = get_task_tags(task_id)

    if not current_tags:
        return

    new_tags = [tag for tag in current_tags if tag not in tags_to_remove]

    if new_tags == current_tags:
        return

    send_bitrix_request('tasks.task.update', {
        'taskId': task_id,
        'fields': {
            'TAGS': new_tags
        }
    })


def get_task(task_id):
    """Читаем задачу по ID."""
    task_response = send_bitrix_request('tasks.task.get', {
        'taskId': task_id,
        'select': ['*', 'UF_*']
    })

    if not task_response or 'task' not in task_response or not task_response['task']:
        return None

    return task_response['task']


def normalize_task_list_response(response):
    """
    Приводим ответ tasks.task.list к списку задач.

    В разных местах/обертках Bitrix может вернуть:
    - сразу список задач;
    - словарь {'tasks': [...], 'total': ...};
    - словарь {'result': {'tasks': [...]}};
    - пустой результат.
    """
    if not response:
        return []

    if isinstance(response, list):
        return response

    if isinstance(response, dict):
        if isinstance(response.get('tasks'), list):
            return response.get('tasks')

        result = response.get('result')
        if isinstance(result, dict) and isinstance(result.get('tasks'), list):
            return result.get('tasks')

        if isinstance(result, list):
            return result

    return []


def find_blocked_lk_tasks(company_id):
    """
    Ищем отложенные задачи ЛК по компании.
    По тегу здесь не фильтруем, чтобы не зависеть от особенностей фильтра задач Битрикс24.
    Тег проверяем отдельно по каждой найденной задаче.
    """
    tasks_response = send_bitrix_request('tasks.task.list', {
        'order': {
            'ID': 'DESC'
        },
        'filter': {
            'GROUP_ID': GROUP_LK,
            'STAGE_ID': LK_STAGE_DEFERRED,
            'UF_CRM_TASK': ['CO_' + company_id]
        },
        'select': ['ID', 'TITLE', 'GROUP_ID', 'STAGE_ID', 'RESPONSIBLE_ID', 'UF_CRM_TASK', 'STATUS']
    })

    tasks = normalize_task_list_response(tasks_response)

    if not tasks:
        return []

    blocked_tasks = []
    for task in tasks:
        if not isinstance(task, dict):
            continue

        task_id = task.get('id') or task.get('ID')
        if not task_id:
            continue

        tags = get_task_tags(task_id)
        if TAG_LIMIT_BLOCK in tags:
            blocked_tasks.append(task)

    return blocked_tasks


def unlock_lk_task(lk_task, overlimit_task):
    """Возвращаем одну задачу ЛК в работу."""
    overlimit_stage_id = str(overlimit_task.get('stageId', ''))
    overlimit_url = get_task_url(overlimit_task)

    send_bitrix_request('tasks.task.update', {
        'taskId': lk_task.get('id') or lk_task.get('ID'),
        'fields': {
            'STAGE_ID': LK_STAGE_NEW
        }
    })

    remove_task_tags(lk_task, [TAG_LIMIT_BLOCK])

    add_task_comment(
        lk_task.get('id') or lk_task.get('ID'),
        f'Задача автоматически возвращена в стадию "Новые".\n\n'
        f'По превышению принято решение, стадия задачи превышения: {overlimit_stage_id}.\n'
        f'Задача превышения:\n{overlimit_url}'
    )


def unlock_lk_tasks_by_overlimit(req):
    """
    Основная функция для вызова через custom_webhook.

    Пример:
    /bitrix/custom_webhook?job=unlock_lk_tasks_by_overlimit&task_id={{ID}}
    """
    try:
        task_id = get_request_value(req, 'task_id') or get_request_value(req, 'TASK_ID') or get_request_value(req, 'id')
        if not task_id:
            print('unlock_lk_tasks_by_overlimit: task_id is empty')
            return

        overlimit_task = get_task(task_id)
        if not overlimit_task:
            print(f'unlock_lk_tasks_by_overlimit: task {task_id} not found')
            return

        if str(overlimit_task.get('groupId', '')) != GROUP_OVERLIMIT:
            print(f'unlock_lk_tasks_by_overlimit: task {task_id} is not in overlimit group')
            return

        overlimit_stage_id = str(overlimit_task.get('stageId', ''))
        if overlimit_stage_id not in OVERLIMIT_UNLOCK_STAGES:
            print(f'unlock_lk_tasks_by_overlimit: stage {overlimit_stage_id} is not unlock stage')
            return

        company_id = get_task_company_id(overlimit_task)
        if not company_id:
            print(f'unlock_lk_tasks_by_overlimit: company not found for task {task_id}')
            return

        blocked_lk_tasks = find_blocked_lk_tasks(company_id)
        if not blocked_lk_tasks:
            print(f'unlock_lk_tasks_by_overlimit: no blocked LK tasks for company {company_id}')
            return

        unlocked_urls = []
        for lk_task in blocked_lk_tasks:
            unlock_lk_task(lk_task, overlimit_task)
            unlocked_urls.append(get_task_url(lk_task))

        if unlocked_urls:
            add_task_comment(
                overlimit_task.get('id') or overlimit_task.get('ID'),
                'Автоматически возвращены в работу задачи ЛК:\n' + '\n'.join(unlocked_urls)
            )

        print(f'unlock_lk_tasks_by_overlimit: unlocked {len(unlocked_urls)} tasks for company {company_id}')
        return {
            'company_id': company_id,
            'unlocked_count': len(unlocked_urls),
            'unlocked_urls': unlocked_urls,
        }

    except Exception as e:
        print(f'Error in unlock_lk_tasks_by_overlimit: {e}')
        return
#2026-05-03 Разблокировка задач ЛК по превышению -- КОНЕЦ
