from time import sleep

from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication
from web_app_4dk.tools import send_bitrix_request


b = Bitrix(authentication('Bitrix'))
#способы доставки документов
documents_delivery = {
        '69': '1581', #ЭДО
        '71': '1583', #Печатные
        '': '',
        None: '',
    }


def fill_act_document_smart_process(req):
    bad_counter = 0
    new_companies = list()
    users = b.get_all('user.get', {
        'filter': {
            '!UF_USR_1690373869887': None #получаем инфо по всем юзерам, у которых заполнено поле СОУ в профиле
        }
    })
    filters = [
        {'assignedById': ['91']} #ИД дежурного администратора
    ]
    for element_filter in filters:
        elements = b.get_all('crm.item.list', {
            'entityTypeId': '161', # ид этого СП
            'filter': element_filter
        })
        if not elements:
            send_bitrix_request('im.notify.system.add', {
                'USER_ID': '1',
                'MESSAGE': f'Было обновлено 0 элементов РТиУ'
            })
            return

        for element in elements:
            sleep(1)
            company_info = send_bitrix_request('crm.company.list', {
                'select': ['*', 'UF_*'],# выбираем все поля сущности
                'filter': {
                    'UF_CRM_1656070716': element['ufCrm41_1689103279'] #служИНН == ИНН в элементе СП
                }
            })
            update_fields = dict()
            if company_info:
                update_fields['companyId'] = company_info[0]['ID']
                update_fields['ufCrm41_1689862848017'] = documents_delivery[company_info[0]['UF_CRM_1638093692254']] #способ доставки
                update_fields['observers'] = company_info[0]['ASSIGNED_BY_ID'] #наблюдатель в элементе == ответственный в компании
                update_fields['ufCrm41_1690546413'] = company_info[0]['TITLE'] #название
            update_fields['ufCrm41_1690807843'] = int(element['ufCrm41_1689101306'].split('-')[-1]) #номер в 1С
            update_fields['assignedById'] = '91'  # задаем
            if element['ufCrm41_1690546413']: #если заполнено название компании в элементе
                user_b24 = list(filter(lambda x: element['ufCrm41_1690283806'] == x['UF_USR_1690373869887'], users)) #находим инфо о пользователе, по значению поля СОУ в элементе мы ищем пользователя, в профиле есть поле СОУ
                if user_b24:
                    update_fields['assignedById'] = user_b24[0]['ID'] #указываем юзера, если найден

            if element_filter == {'assignedById': ['91']} and update_fields['assignedById'] == '91':
                bad_counter += 1

            if update_fields['assignedById'] == '91':
                if element['ufCrm41_1690283806'] == '4f4d8faa-c928-11e6-8a6d-aa3d71163f04':# для Александровой и Васильчука - ВМА и МЕБ
                    update_fields['assignedById'] = '169'
                elif element['ufCrm41_1690283806'] == 'e0677df2-dd6e-11e6-8e7c-0050569f0c3a':
                    update_fields['assignedById'] = '161'

            if (element['stageId'] == 'DT161_53:NEW' or element['stageId'] == 'DT161_53:1') and element['ufCrm41_1689101216']:#если первая или вторая стадия и заполнена дата сдачи, то перевод в завершенные
                update_fields['stageId'] = 'DT161_53:SUCCESS'

            send_bitrix_request('crm.item.update', { #обновлеям в б24
                'entityTypeId': '161',
                'id': element['id'],
                'fields': update_fields
            })

            if not company_info: #создание псевдо-компании для отправки задачи администраторам
                company = send_bitrix_request('crm.company.add', {
                    'fields': {
                        'TITLE': element['ufCrm41_1689103279'], #ИНН
                        'ASSIGNED_BY_ID': update_fields['assignedById'],
                        'UF_CRM_1656070716': element['ufCrm41_1689103279'], #служИНН
                        'COMPANY_TYPE': 'CUSTOMER'
                    }
                })
                new_companies.append(f"ИНН: {element['ufCrm41_1689103279']} https://vc4dk.bitrix24.ru/crm/company/details/{company}/\n") #добавить в список в конец если это важно

        if new_companies:
            task = send_bitrix_request('tasks.task.add', {
                'fields': {
                    'TITLE': 'Новые компании РТиУ',
                    'DESCRIPTION': f'При выгрузке РТиУ для следующих компаний не найдено соответствий в Б24, поэтому компании были созданы в Б24:\n\n'
                                   f'{new_companies}',
                    'GROUP_ID': '13',
                    'RESPONSIBLE_ID': '1',
                    'CREATED_BY': '173'

                }
            })['task']['id']

            for row in new_companies:
                b.call('task.checklistitem.add', [task, {'TITLE': row}], raw=True)  #пост-запрос, делаем пункты чек-листа

        #elements = b.get_all('crm.item.list', {
        #    'entityTypeId': '161',
        #    'filter': {
        #        'stageId': 'DT161_53:NEW',
        #        '!ufCrm41_1689101216': None,   # не дата сдачи = пустая
        #    }
        #})
        
        elements = b.get_all('crm.item.list', {
            'entityTypeId': '161',
            'filter': {
                'stageId': ['DT161_53:NEW', 'DT161_53:1'],
                '>ufCrm41_1689101216': '2020-03-19T02:00:00+02:00'   # не дата сдачи = пустая
            }
        })
    for element in elements:
        send_bitrix_request('crm.item.update', { # еще раз переносим в заверщенные те записи. у которых дата сдачи заполнена, но они в "новых"
            'entityTypeId': '161',
            'id': element['id'],
            'fields': {
                'stageId': 'DT161_53:SUCCESS'
            }
        })

    send_bitrix_request('im.notify.system.add', {
        'USER_ID': req['user_id'][5:],
        'MESSAGE': f'Элементы РТиУ заполнены\n'
                   f'Плохих элементов {bad_counter}'})


if __name__ == '__main__':
    fill_act_document_smart_process({'user_id': 'user_1'})
