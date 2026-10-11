"""Настройки учёта. Вебхук берётся из существующего authentication.py."""
from pathlib import Path

# Начало учёта по дате выполненной работы, включительно.
START_DATE = "2026-09-10"
KS_START_DATE = "2026-10-01"
TIMEZONE = "Europe/Moscow"
# Общая папка блокировок для Flask и загрузчика. По умолчанию рядом с этим файлом.
# Запускайте загрузчик от того же пользователя сервера, что и Flask.
LOCK_DIRECTORY = Path(__file__).resolve().parent / "worklog_locks"

SETTINGS = {'list_id': '175',
 'tasks_field': 'PROPERTY_2106',
 'ks_tasks_field': 'PROPERTY_2120',
 'total_field': 'PROPERTY_2108',
 'total_seconds_field': 'PROPERTY_2110',
 'entity_type_id': 1146,
 'category_id': 144,
 'start_date': '2026-09-10',
 'timezone': 'Europe/Moscow',
 'fields': {'source': 'UF_CRM_108_1788974313',
            'key': 'UF_CRM_108_1788974357',
            'task': 'UF_CRM_108_1788974376',
            'url': 'UF_CRM_108_1788974405',
            'entry': 'UF_CRM_108_1788974426',
            'group': 'UF_CRM_108_1788974443',
            'tag': 'UF_CRM_108_1788974458',
            'direction': 'UF_CRM_108_1788974489',
            'employee': 'UF_CRM_108_1788974521',
            'date': 'UF_CRM_108_1788974544',
            'seconds': 'UF_CRM_108_1788974635',
            'description': 'UF_CRM_108_1788974646',
            'period': 'UF_CRM_108_1788974673',
            'kind': 'UF_CRM_108_1788974689',
            'receiver': 'UF_CRM_108_1788974734',
            'state': 'UF_CRM_108_1788974748'},
 'source_id': 2324,
 'active_state': 2334,
 'deleted_state': 2336,
 'review_state': 2338,
 'general_kind': 2328,
 'rules': [
     {'group_id': 1, 'tag': 'ЭПД', 'direction_id': 2326, 'kind_id': 2328,
      'label': 'ЭПД', 'start_date': START_DATE, 'total_field': 'PROPERTY_2106',
      'exclude_company_field': 'UF_CRM_1789223269972', 'excluded_stage_ids': [1767]},
     {'group_id': 1, 'tag': 'КС_Поддержка', 'direction_id': None, 'kind_id': 2328,
      # ID находим по точному названию в crm.item.fields до первой записи.
      'direction_name': 'Кабинет сотрудника', 'label': 'Кабинет сотрудника',
      'start_date': KS_START_DATE, 'total_field': 'PROPERTY_2120',
      'exclude_company_field': 'UF_CRM_1791539662886', 'excluded_stage_ids': [1767]},
 ]}
SETTINGS.update(start_date=START_DATE, timezone=TIMEZONE)
