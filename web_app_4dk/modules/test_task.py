from datetime import datetime, timedelta
from time import time, sleep
from random import randint
import json

from web_app_4dk.tools import send_bitrix_request
from web_app_4dk.chat_bot.SendMessage import bot_send_message


def send_notification(task_info, notification_type):
    users_notification_list = ['339']
    if not task_info or not task_info['auditors']:
        return
    auditors = task_info['auditors']
    task_id = task_info['id']
    flag = False
    for user in users_notification_list:
        if user in auditors:
            if notification_type == 'Создание':
                send_bitrix_request('im.notify.system.add', {'USER_ID': user,
                                                             'MESSAGE': f"Была создана новая задача, в которой вы являетесь наблюдателем:\nhttps://vc4dk.bitrix24.ru/company/personal/user/{user}/tasks/task/view/{task_id}/"})
                send_bitrix_request('im.notify.system.add', {'USER_ID': '1',
                                                             'MESSAGE': f"Была создана новая задача, в которой вы являетесь наблюдателем:\nhttps://vc4dk.bitrix24.ru/company/personal/user/{user}/tasks/task/view/{task_id}/"})
            elif notification_type == 'Завершение':
                send_bitrix_request('im.notify.system.add', {'USER_ID': user,
                                                             'MESSAGE': f"Завершена задача, в которой вы являетесь наблюдателем:\nhttps://vc4dk.bitrix24.ru/company/personal/user/{user}/tasks/task/view/{task_id}/"})
                send_bitrix_request('im.notify.system.add', {'USER_ID': '1',
                                                             'MESSAGE': f"Завершена задача, в которой вы являетесь наблюдателем:\nhttps://vc4dk.bitrix24.ru/company/personal/user/{user}/tasks/task/view/{task_id}/"})
                if not flag:
                    send_bitrix_request('tasks.task.update', {'taskId': task_info['id'], 'fields': {'UF_AUTO_934103382947': '1'}})
                    flag = True


def check_similar_tasks_this_hour2(task_info, company_id):
    users_id = [task_info['createdBy'], '1391']
    if task_info['groupId'] not in ['1', '7']:
        return
    group_names = {
        '1': 'ТЛП',
        '7': 'ЛК',
    }
    time_filter = (datetime.now() + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S') #вычитаем из тек даты 1 час

    similar_tasks = send_bitrix_request('tasks.task.list', {
        'filter': {
            '!ID': task_info['id'],
            '>=CREATED_DATE': time_filter,
            'GROUP_ID': task_info['groupId'],
            'UF_CRM_TASK': ['CO_' + company_id]
        }
    })

    if not similar_tasks:
        return

    similar_tasks_url = '\n'.join(tuple(map(lambda x: f"https://vc4dk.bitrix24.ru/workgroups/group/{task_info['groupId']}/tasks/task/view/{x['id']}/", similar_tasks)))
    if similar_tasks:
        for user_id in users_id:
            send_bitrix_request('im.notify.system.add', {
                'USER_ID': user_id,
                'MESSAGE': f"Для текущей компании в группе {group_names[task_info['groupId']]} уже были поставлены задачи за прошедший час\n"
                           f"Новая задача: https://vc4dk.bitrix24.ru/workgroups/group/{task_info['groupId']}/tasks/task/view/{task_info['id']}/\n\n"
                           f"Поставленные ранее:\n {similar_tasks_url}"
            })


def task_registry2(task_info, event):
    sleep(randint(1, 30))
    task_status = {
        "2": 343, #поле в реестре задач Статусзадачи, у каждого знч поля есть свой id
        "-1": 345,
        "-3": 347,
        "3": 349,
        "4": 351,
        "5": 353,
        "6": 355,
    }

    if task_info['groupId'] and task_info['groupId'] != '0':
        groupid=task_info['groupId']
        taskinfo=task_info['id']
        task_url = f'<a href="https://vc4dk.bitrix24.ru/workgroups/group/{groupid}/tasks/task/view/{taskinfo}/">Ссылка на задачу</a>'
    else:
        respid = task_info['responsibleId']
        taskinfo=task_info['id']
        task_url = f'<a href="https://vc4dk.bitrix24.ru/company/personal/user/{respid}/tasks/task/view/{taskinfo}/">Ссылка на задачу</a>'





    company_id = ''
    contact_id = ''
    if 'ufCrmTask' in task_info and task_info['ufCrmTask']:
        ufCrmCompany = list(filter(lambda x: 'CO_' in x, task_info['ufCrmTask']))
        if ufCrmCompany:
            company_id = ufCrmCompany[0][3:]

        ufCrmContact = list(filter(lambda x: 'C_' in x, task_info['ufCrmTask']))
        #print(task_info)
        if ufCrmContact:
            contact_id = ufCrmContact[0][2:]


    groups = send_bitrix_request('sonet_group.get', {})  #получили инфо по всем группам, что есть на портале
    try:
        group_name = list(filter(lambda x: task_info['groupId'] == x['ID'], groups))[0]['NAME'] # ищем по id группу и берем ее название
    except:
        group_name = ''

    tags = send_bitrix_request('task.item.gettags', {'taskId': task_info['id']})
    if tags:
        tags = ', '.join(tags) #изначально теги в виде листа, а этой операцией мы переделываем в строку с сепаратором ,
    else:
        tags = ''
    registry_element = send_bitrix_request('lists.element.get', { #получаем элемент списка по ид задачи
        'IBLOCK_TYPE_ID': 'lists',
        'IBLOCK_ID': '107',
        'FILTER': {
            'PROPERTY_517': task_info['id'],
        }
    })
    if registry_element: # если нашли, то обновляем
        registry_element = registry_element[0]
        send_bitrix_request('lists.element.update', {
            "IBLOCK_TYPE_ID": "lists",
            "IBLOCK_ID": "107",
            "ELEMENT_ID": registry_element['ID'],
            "FIELDS": {
                "NAME": task_info["title"],
                "PROPERTY_517": task_info['id'],
                "PROPERTY_495": task_status[task_info['status']],
                "PROPERTY_499": company_id,
                "PROPERTY_501": contact_id,
                "PROPERTY_537": group_name,
                "PROPERTY_505": task_info["createdDate"],
                "PROPERTY_507": task_info["closedDate"],
                "PROPERTY_509": task_info["createdBy"],
                "PROPERTY_511": task_info["responsibleId"],
                "PROPERTY_515": tags,
                "PROPERTY_513": task_info["durationFact"],
                "PROPERTY_1747": task_url
            }})
    elif event == 'ONTASKADD':
        registry_element = send_bitrix_request('lists.element.get', {
            'IBLOCK_TYPE_ID': 'lists',
            'IBLOCK_ID': '107',
            'FILTER': {
                'PROPERTY_517': task_info['id'],
            }
        })
        if registry_element:
            return

        new_element = send_bitrix_request('lists.element.add', {
            "IBLOCK_TYPE_ID": "lists",
            "IBLOCK_ID": "107",
            "ELEMENT_CODE": task_info['id'],
            "FIELDS": {
                "NAME": task_info["title"],
                "PROPERTY_517": task_info['id'],
                "PROPERTY_495": task_status[task_info['status']],
                "PROPERTY_499": company_id,
                "PROPERTY_501": contact_id,
                "PROPERTY_537": group_name,
                "PROPERTY_505": task_info["createdDate"],
                "PROPERTY_507": task_info["closedDate"],
                "PROPERTY_509": task_info["createdBy"],
                "PROPERTY_511": task_info["responsibleId"],
                "PROPERTY_515": tags,
                "PROPERTY_513": task_info["durationFact"],
                "PROPERTY_1747": task_url

            }})

        if task_info["responsibleId"] == '157':
            bot_send_message({'dialog_id': '157',
                              'message': f"Была создана новая задача, в которой вы являетесь ответственным:\nhttps://vc4dk.bitrix24.ru/company/personal/user/157/tasks/task/view/{task_info['id']}/"})


def fill_task_title2(req, event):
    task_id = req['task_id']
    task_info = send_bitrix_request('tasks.task.get', { # читаем инфо о задаче
        'taskId': task_id,
        'select': ['*', 'UF_AUTO_324910901949', 'UF_*']
    })

    if not task_info or 'task' not in task_info or not task_info['task']: # если задача удалена или в иных ситуациях
        return

    task_info = task_info['task']

    task_registry2(task_info, event)
    '''
    if task_info['closedDate'] and task_info['ufAuto934103382947'] != '1':
        send_notification(task_info, 'Завершение')
    '''

    if 'ufCrmTask' not in task_info or not task_info['ufCrmTask']: # ufCrmTask - связь с сущностью (список)
        return
    

    #2025-07-29 САА начало
    if task_info['groupId'] == '1' and task_info['stageId'] == '11':
            print(1)
            print(task_info['UF_AUTO_324910901949'])
            if task_info['UF_AUTO_324910901949'] != '1':
                print(2)
                contact_crm = list(filter(lambda x: 'C_' in x, task_info['ufCrmTask']))
                if not contact_crm:
                    return

                print(3)
            
                contact_info = send_bitrix_request('crm.contact.get', { 
                    'select': ['UF_CRM_1752841613', 'UF_CRM_1750926740'], #поля вип в компании и вип
                    'filter': {
                        'ID': contact_crm
                    }
                })

                if contact_info['UF_CRM_1752841613'] == 1 and contact_info['UF_CRM_1750926740'] == 1:
                    print(4)
                    send_bitrix_request('tasks.task.update', {
                    'taskId': task_id,
                    'fields': {
                        'stageId': '2367',
                        'UF_AUTO_324910901949': 1
                        }})
    #2025-07-29 САА конец

    company_crm = list(filter(lambda x: 'CO' in x, task_info['ufCrmTask']))
    uf_crm_task = []

    if not company_crm:
        contact_crm = list(filter(lambda x: 'C_' in x, task_info['ufCrmTask']))
        if not contact_crm:
            return
#2024-07-19 временно отключим
        '''
        # если к задаче прикреплен только контакт
        contact_crm = contact_crm[0][2:]
        main_company = send_bitrix_request('crm.contact.get', {'id': contact_crm})['UF_CRM_1692058520'] # читаем поле Основная компания

        if main_company: # если основная компания заполнена, то читаем у неё поле Тип компании
            company_info = send_bitrix_request('crm.company.get', {'id': main_company, 'select': ['COMPANY_TYPE']})

            if company_info['COMPANY_TYPE'] not in ['UC_E99TUC']: # если тип компании != Закончился ИТС
                company_id = main_company
                uf_crm_task = ['CO_' + company_id, 'C_' + contact_crm] # нельзя дописать, можно только перезаписать обоими значениями заново

        if not main_company or company_info['COMPANY_TYPE'] in ['UC_E99TUC']: # если нет основной компании или у неё закончился ИТС

            contact_companies = list(map(lambda x: x['COMPANY_ID'], send_bitrix_request('crm.contact.company.items.get', {'id': contact_crm})))
            if not contact_companies: # если нет привязанных компаний к контакту
                return
            contact_companies_info = send_bitrix_request('crm.company.list', { # читаем вес сделок всех компаний, привязанных к контакту
                'select': ['COMPANY_TYPE', 'UF_CRM_1660818061808'],     # Тип компании и Вес сделок
                'filter': {
                    'ID': contact_companies
                }
            })

            active_companies = list(filter(lambda x: x['COMPANY_TYPE'] != 'UC_E99TUC', contact_companies_info)) # собираем компании с действующим ИТС

            if active_companies: # если есть привязанные компании с действующим ИТС
                for i in range(len(active_companies)):
                    if not active_companies[i]['UF_CRM_1660818061808']: # если поле Вес не заполнено, то проставляем 0
                        active_companies[i]['UF_CRM_1660818061808'] = 0
                best_value_company = list(sorted(active_companies, key=lambda x: float(x['UF_CRM_1660818061808'])))[-1]['ID'] # последний элемент в общем списке - с макс value
                uf_crm_task = ['CO_' + best_value_company, 'C_' + contact_crm] # нельзя дописать, можно только перезаписать обоими значениями заново
                company_id = best_value_company # это для тайтла

            elif contact_companies_info: # если есть привязанные компании с НЕ действующим ИТС
                for i in range(len(contact_companies_info)):
                    if not contact_companies_info[i]['UF_CRM_1660818061808']: # если поле Вес не заполнено, то проставляем 0
                        contact_companies_info[i]['UF_CRM_1660818061808'] = 0
                best_value_company = list(sorted(contact_companies_info, key=lambda x: float(x['UF_CRM_1660818061808'])))[-1]['ID'] # последний элемент в общем списке - с макс value
                uf_crm_task = ['CO_' + best_value_company, 'C_' + contact_crm] # нельзя дописать, можно только перезаписать обоими значениями заново
                company_id = best_value_company # это для тайтла
        '''
        contact_crm = contact_crm[0][2:]


        contact_companies = list(map(lambda x: x['COMPANY_ID'], send_bitrix_request('crm.contact.company.items.get', {'id': contact_crm})))

        if not contact_companies: # если нет привязанных компаний к контакту
            return
        contact_companies_info = send_bitrix_request('crm.company.list', { # читаем вес сделок всех компаний, привязанных к контакту
            'select': ['COMPANY_TYPE', 'UF_CRM_1660818061808'],     # Тип компании и Вес сделок
            'filter': {
                'ID': contact_companies
            }
        })

        active_companies = list(filter(lambda x: x['COMPANY_TYPE'] != 'UC_E99TUC', contact_companies_info)) # собираем компании с действующим ИТС

        if active_companies: # если есть привязанные компании с действующим ИТС
            for i in range(len(active_companies)):
                if not active_companies[i]['UF_CRM_1660818061808']: # если поле Вес не заполнено, то проставляем 0
                    active_companies[i]['UF_CRM_1660818061808'] = 0
            best_value_company = list(sorted(active_companies, key=lambda x: float(x['UF_CRM_1660818061808'])))[-1]['ID'] # последний элемент в общем списке - с макс value
            uf_crm_task = ['CO_' + best_value_company, 'C_' + contact_crm] # нельзя дописать, можно только перезаписать обоими значениями заново
            company_id = best_value_company # это для тайтла

        elif contact_companies_info: # если есть привязанные компании с НЕ действующим ИТС
            for i in range(len(contact_companies_info)):
                if not contact_companies_info[i]['UF_CRM_1660818061808']: # если поле Вес не заполнено, то проставляем 0
                    contact_companies_info[i]['UF_CRM_1660818061808'] = 0
            best_value_company = list(sorted(contact_companies_info, key=lambda x: float(x['UF_CRM_1660818061808'])))[-1]['ID'] # последний элемент в общем списке - с макс value
            uf_crm_task = ['CO_' + best_value_company, 'C_' + contact_crm] # нельзя дописать, можно только перезаписать обоими значениями заново
            company_id = best_value_company # это для тайтла

#2024-07-19 конец вставки

    else:
        company_id = company_crm[0][3:]


    if event == 'ONTASKADD':
        check_similar_tasks_this_hour2(task_info, company_id)

    company_info = send_bitrix_request('crm.company.get', { # читаем инфо о найденной компании
        'ID': company_id,
    })

    if company_info and company_info['TITLE'].strip() in task_info['title']: # strip() - очищает от пробелов по краям, если есть название компании в тайтле, то возрват
        return

    if not uf_crm_task: #если не заполнено CRM - если в задаче уже есть company_id и нам не нужно ее заполнять
        #ВМА
        if company_info['ASSIGNED_BY_ID'] in ['169','177','185','131','135','355','181','175','129'] and task_info['groupId'] in ['23','9']:
            audit = task_info['auditors']
            audit.append('169')
            send_bitrix_request('tasks.task.update', {
                'taskId': task_id,
                'fields': {
                    'TITLE': f"{task_info['title']} {company_info['TITLE']}",
                    'AUDITORS': audit
                    }})
        else:
            send_bitrix_request('tasks.task.update', {
                'taskId': task_id,
                'fields': {
                    'TITLE': f"{task_info['title']} {company_info['TITLE']}"
                    }})
    #2024-01-21
    elif "Пропущен звонок от клиента" in task_info["title"]:
        instead = task_info['auditors']
        send_bitrix_request('tasks.task.update', {
            'taskId': task_id,
            'fields': {
                'TITLE': f"{task_info['title']} {company_info['TITLE']}",
                'UF_CRM_TASK': uf_crm_task,
                'GROUP_ID': '167',
                'CREATED_BY': '173',
                'RESPONSIBLE_ID': task_info['auditors'][0]
            }})
    #добавление ВМА как наблюдателя
    elif company_info['ASSIGNED_BY_ID'] in ['169','177','185','131','135','355','181','175','129'] and task_info['groupId'] in ['23','9']:
        audit = task_info['auditors']
        audit.append('169')
        send_bitrix_request('tasks.task.update', {
            'taskId': task_id,
            'fields': {
                'TITLE': f"{task_info['title']} {company_info['TITLE']}",
                'UF_CRM_TASK': uf_crm_task,
                'AUDITORS': audit
            }})
    else:
        send_bitrix_request('tasks.task.update', {
            'taskId': task_id,
            'fields': {
                'TITLE': f"{task_info['title']} {company_info['TITLE']}",
                'UF_CRM_TASK': uf_crm_task,
            }})


def task_handler2(req, event=None):
    try:
        task_info = fill_task_title2(req, event)
    except:
        return
    '''
    send_notification(task_info, 'Создание')
    '''
