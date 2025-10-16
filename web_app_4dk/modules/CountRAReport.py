from datetime import datetime, timedelta
from time import sleep
import base64
import requests
from fast_bitrix24 import Bitrix
from web_app_4dk.modules.authentication import authentication
#from authentication import authentication

b = Bitrix(authentication('Bitrix'))

def get_employee_id(users: str) -> list:
    """
    Приводит строку с id пользователей и id подразделений к единому списку, состоящему только из id сотрудников

    :param users: Строка из параметра запроса Б24 состоящая из {user_...} и|или {group_...}, которые разделены ', '
    """

    users_id_set = set()

    # Строка с сотрудниками и отделами в список
    users = users.split(', ')

    # Если в массиве найден id сотрудника
    for user_id in users:
        if 'user' in user_id:
            users_id_set.add(user_id[5:])

        # Если в массиве найден id отдела
        elif 'group' in user_id:
            department_users = b.get_all('user.get', {'filter': {'UF_DEPARTMENT': user_id[8:]}})
            for user in department_users:
                users_id_set.add(user['ID'])

    return list(users_id_set)

def get_fio_from_user_info(user_info: dict) -> str:
    """
    Возвращает строку, состоящую из фамилии и имени пользователя Б24

    :param user_info: Словарь, полученный запросом с методом user.get
    """

    return (f'{user_info["LAST_NAME"] if "LAST_NAME" in user_info else ""}'
            f' {user_info["NAME"] if "NAME" in user_info else ""}').strip()

def count_ra_report(req):

    report_day = datetime.now() - timedelta(days=1)
    day_title = datetime.strftime(report_day, '%d.%m.%y')
    report_day = datetime.strftime(report_day, '%Y-%m-%d') + 'T00:00:00+03:00' #начало текущего дня

    users_info_cs = b.get_all('user.get', {
            'filter': {
                'ACTIVE': 1,
                'UF_DEPARTMENT': ['5', '27', '29'] #ЦС, ГО3, ГО4
            }
        })
    users_id_cs = list(set(map(lambda x: int(x['ID']), users_info_cs)))
    
    users_info_lk = b.get_all('user.get', {
            'filter': {
                'ACTIVE': 1,
                'UF_DEPARTMENT': ['231'] #ЛК
            }
        })
    users_id_lk = list(set(map(lambda x: int(x['ID']), users_info_lk)))

    except_user = ['91'] #юзеры-исключения: дежурный админ

    connect = b.get_all('crm.item.list', { #смарт-процесс Подключения 1С-Коннект
                'entityTypeId': '1090',
                'filter': {
                    '>=ufCrm81_1760192180': report_day
                    }})

    if connect:
        users_connect = list(set(map(lambda x: x['ufCrm81_1760192006'], connect))) #собираем всех подключавшихся
        text_message_lk = f'[b]Подключения по коннекту ЛК за {day_title}[/b]\n\n' #заголовок отчета по лк
        text_message_cs = f'[b]Подключения по коннекту за {day_title}[/b]\n\n' #заголовок отчета по цс
        flag_cs = 0
        flag_lk = 0

        for user_connect in users_connect:
            if user_connect not in except_user:
                if user_connect in users_id_cs:
                    
                    user_info = list(filter(lambda x: int(x['ID']) == user_connect, users_info_cs))[0]
                    user_name = get_fio_from_user_info(user_info)

                    duration_connect = 0
                    connect_user = list(filter(lambda x: x['ufCrm81_1760192006'] == user_connect, connect))

                    if connect_user:
                        count_connect = len(connect_user)
                        for i in connect_user:
                            duration_connect += i['ufCrm81_1760192221']
                        duration_connect = round(duration_connect / 60)
                        text_message_cs += f'{user_name} {count_connect} ({duration_connect} мин)\n'
                        flag_cs = 1
                    
                elif user_connect in users_id_lk:
                    
                    user_info = list(filter(lambda x: int(x['ID']) == user_connect, users_info_lk))[0]
                    user_name = get_fio_from_user_info(user_info)

                    duration_connect = 0
                    connect_user = list(filter(lambda x: x['ufCrm81_1760192006'] == user_connect, connect))

                    if connect_user:
                        count_connect = len(connect_user)
                        for i in connect_user:
                            duration_connect += i['ufCrm81_1760192221']
                        duration_connect = round(duration_connect / 60)
                        text_message_lk += f'{user_name} {count_connect} ({duration_connect} мин)\n'
                        flag_lk = 1

        #print(text_message_cs)
        #print(text_message_lk)

        if flag_cs == 0:
            text_message_cs += f'Подключений за текущий день не найдено'
        if flag_lk == 0:
            text_message_lk += f'Подключений за текущий день не найдено'

        #отправка отчета по ЦС в чат chat18303
        data_cs = {
            'DIALOG_ID': '1391',
            'MESSAGE': text_message_cs,
            }
        r = requests.post(url=f'{authentication("user_173").strip()}im.message.add', json=data_cs)
        
        #отправка отчета по ЛК для СЮВ, ИБС и САА 19
        notification_users = ['1391']
        for user in notification_users:
            data_lk = {
                'DIALOG_ID': user,
                'MESSAGE': text_message_lk,
            }
            r = requests.post(url=f'{authentication("user_173").strip()}im.message.add', json=data_lk)

        #отправка отчета по ЛК от службы качества чдк для СНА 157
        data = {
            'DIALOG_ID': '1391',
            'MESSAGE': text_message_lk,
        }
        r = requests.post(url=f'{authentication("user_639").strip()}im.message.add', json=data)        

    else:
        users_id = ['1391', '1'] # ДОБАВИТЬ ИБС
        for user_id in users_id:
            b.call('im.notify.system.add', {
                'USER_ID': user_id,
                'MESSAGE': f'Подключений по коннекту за текущий день не найдено, отчеты по ЛК и ЦС не отправлены.'})
        

if __name__ == '__main__':
    count_ra_report()