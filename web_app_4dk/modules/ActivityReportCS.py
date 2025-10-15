from datetime import datetime, timedelta
from time import sleep
import base64
import requests
from fast_bitrix24 import Bitrix
#from web_app_4dk.modules.authentication import authentication
from authentication import authentication

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

def activity_report_cs():

    report_day = datetime.now()
    day_title = datetime.strftime(report_day, '%d.%m.%y')
    report_day = datetime.strftime(report_day, '%Y-%m-%d') + 'T00:00:00+03:00' #начало текущего дня

    start_of_month = datetime.now()
    start_of_month = f"{datetime.strftime(start_of_month, '%Y-%m')}-01"
    start_of_month = start_of_month + 'T00:00:00+03:00' #начало текущего месяца

    users_info = b.get_all('user.get', {
            'filter': {
                'ACTIVE': 1,
                'UF_DEPARTMENT': ['5', '27', '29'] #ЦС, ГО3, ГО4
            }
        })
    except_user = ['91'] #юзеры-исключения: дежурный админ
    
    timespent_report = f'[b]Трудозатраты по работам ИТС за {day_title} (Время / Кол-во)[/b]\n\n' #заголовок отчета

    for user_info in users_info:
        if user_info['ID'] not in except_user:

            user_name = get_fio_from_user_info(user_info)

            #вытаскиваем трудозатраты сотрудника за сегодня
            sec_timespent = 0
            results = b.call('task.elapseditem.getlist', {
                'order': {'ID': 'asc'},
                'filter': {
                    'USER_ID': user_info['ID'],
                    '>=CREATED_DATE': report_day}
                }, raw=True)['result']

            if len(results) > 49:
                users_id = ['1391', '1']
                for user_id in users_id:
                    b.call('im.notify.system.add', {
                        'USER_ID': user_id,
                        'MESSAGE': f'У сотрудника [b]{user_name}[/b] количество трудозатрат за день достигло 50 записей.\n Отчет по трудозатратам в чате ЦС некорректен.'})
            
            if results:
                tasks_id = list(map(lambda x: x['TASK_ID'], results)) #список id задач из списка трудозатрат

                task_work_its = b.get_all('tasks.task.list', { #задачи из группы РаботыИТС по которым были трудозатраты
                'filter': {
                    'ID': tasks_id,
                    'GROUP_ID': '321'
                    }})
                id_task_work_its = list(map(lambda x: x['id'], task_work_its)) #id задач из группы РаботыИТС с трудозатратами

                timespent_user = list(filter(lambda x: x['TASK_ID'] in id_task_work_its, results)) #трудозатраты из задач РаботыИТС

                for t in timespent_user:
                    sec_timespent += int(t['SECONDS'])
        
                if sec_timespent > 0:
                    count_timespent = len(timespent_user) #количество записей о затратах
                    sum_timespent = str(timedelta(seconds=sec_timespent)) #сумма затрат
                    timespent_report += f'{user_name} {sum_timespent} / {count_timespent}\n' #строка с показаниями сотрудника
                    
    #print(timespent_report)

    # ниже кусок кода, оставленный на случай, если мы упремся в лимит 50 записей о трудозатратах в день
    ''' 
    #вытаскиваем все задачи за текущий месяц из РаботыИТС
    task_work_its = b.get_all('tasks.task.list', {
    'filter': {
        '>=CREATED_DATE': start_of_month,
        'GROUP_ID': '321'
        }})
    
    timespent_report = f'[b]Трудозатраты по работам ИТС за {day_title}[/b]\n\n' #заголовок отчета

    for user_info in users_info:
        if user_info['ID'] not in except_user:

            user_name = get_fio_from_user_info(user_info)

            task_user = list(filter(lambda x: x['responsibleId'] == user_info['ID'], task_work_its)) #все задачи пользователя
            tasks_id = list(map(lambda x: x['id'], task_user))

            if task_user:

                #вытаскиваем трудозатраты за сегодня из этих задач
                timespent_user = list()
                sec_timespent = 0
                for i in tasks_id:
                    results = b.call('task.elapseditem.getlist', {
                        'TASKID': i,
                        'order': {'ID': 'asc'},
                        'filter': {
                            'USER_ID': user_info['ID'],
                            '>=CREATED_DATE': report_day}
                        }, raw=True)['result']
                    
                    if results:
                        timespent_user.extend(results)
                        for t in results:
                            sec_timespent += int(t['SECONDS'])
                
                if sec_timespent > 0:
                    count_timespent = len(timespent_user) #количество записей о затратах
                    sum_timespent = str(timedelta(seconds=sec_timespent)) #сумма затрат
                    timespent_report += f'{user_name} {sum_timespent} / {count_timespent}\n' #строка с показаниями сотрудника
    
            sleep(1)
    '''

    #рассылка от робота задач
    #notification_users = [user_info['ID'], '1', '1391'] chat18303
    notification_users = ['1391']
    for user in notification_users:
        data = {
            'DIALOG_ID': user,
            'MESSAGE': timespent_report,
        }

        r = requests.post(url=f'{authentication("user_173").strip()}im.message.add', json=data)
        
if __name__ == '__main__':
    activity_report_cs()