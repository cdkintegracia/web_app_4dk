import base64
from fast_bitrix24 import Bitrix
from authentication import authentication

b = Bitrix(authentication('Bitrix'))


# Кэш пользователей
users_cache = {}
def get_user_name(user_id):

    if user_id in users_cache:
        return users_cache[user_id]

    user = b.call(
        'user.get',
        {
            'ID': user_id
        }
    )

    if user:

        user_name = (
            f'{user.get("LAST_NAME", "")} '
            f'{user.get("NAME", "")}'
        ).strip()

    else:
        user_name = str(user_id)

    users_cache[user_id] = user_name

    return user_name

def list_contacts_city_phone():

    result = []

    # Получаем только контакты без компании с заполненными телефонами
    contacts = b.get_all(
        'crm.contact.list',
        {
            'filter': {
                'COMPANY_ID': False,
                '!PHONE': False
            },
            'select': ['ID', 'PHONE', 'LAST_NAME', 'NAME', 'SECOND_NAME', 'ASSIGNED_BY_ID']
        }
    )

    for contact in contacts:

        manager_name = get_user_name(contact.get('ASSIGNED_BY_ID'))

        fio = (f'{contact.get("LAST_NAME", "")}, {contact.get("NAME", "")}, {contact.get("SECOND_NAME", "")}' ).strip()
        phones = contact.get('PHONE', [])

        if not phones:
            continue
        city_phones = []

        for phone in phones:

            value = phone.get('VALUE', '')

            # Нормализуем номер
            normalized = (
                value.replace(' ', '')
                     .replace('-', '')
                     .replace('(', '')
                     .replace(')', '')
                     .replace('+', '')
            )

            # Проверяем городской номер СПб
            if normalized.startswith(('812', '7812')):
                city_phones.append(value)

        # Если городских номеров нет — пропускаем
        if not city_phones:
            continue

        result.append({
                    'manager': manager_name,
                    'fio': fio,
                    'phones': ', '.join(city_phones),
                    'link': (f'https://vc4dk.bitrix24.ru/crm/contact/details/{contact.get("ID")}/')
                })

    
    result.sort(key=lambda x: x['manager']) #сортировка по менеджеру

    # Формируем сообщение
    if result:

        message_lines = []
        for index, item in enumerate(result, start=1):

            message_lines.append(
                f'{index}. '
                f'{item["manager"]} - '
                f'{item["fio"]} - '
                f'{item["phones"]} - '
                f'{item["link"]}'
            )

        message = '\n\n'.join(message_lines)

    else:
        message = ('Контактов без компаний с городскими номерами не найдено.')

    # Отправляем уведомления
    #users_id = ['1391', '1']
    users_id = ['1391']
    for user_id in users_id:
        b.call(
            'im.notify.system.add',
            {
                'USER_ID': user_id,
                'MESSAGE': message
            }
        )

if __name__ == '__main__':
    list_contacts_city_phone()