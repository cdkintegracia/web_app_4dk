from datetime import datetime

from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication
from web_app_4dk.chat_bot.SendMessage import bot_send_message


# Считывание файла authentication.txt
webhook = authentication('Bitrix')
b = Bitrix(webhook)


int_to_month = {
    1: 'Январь',
    2: 'Февраль',
    3: 'Март',
    4: 'Апрель',
    5: 'Май',
    6: 'Июнь',
    7: 'Июль',
    8: 'Август',
    9: 'Сентябрь',
    10: 'Октябрь',
    11: 'Ноябрь',
    12: 'Декабрь'
}

def check_task_result(dct):
    if 'group_id' in dct:
        if dct['group_id'] == '89':
            stage_comments = {
                '1269': 'Вы взяли задачу в работу. Позвоните пользователю, уточните, использует ли он в работе сервис, и получена ли подпись ФНС.',
                '1275': 'Кратко объясните пользователю последствия, зафиксируйте дату следующего контакта в поле крайнего срока или в комментарии',
                '1271': 'Требуется создать заявление на изменение, используя подпись ФНС, дождитесь обработки заявления (сообщите в офис о создании заявления) и завершите задачу',
                '1273': 'Пользователь не в курсе, получена или нет подпись. Зафиксируйте дату следующего контакта в поле крайнего срока или в комментарии',
            }
            b.call('task.commentitem.add', [dct['id'], {'POST_MESSAGE': stage_comments[dct['stage_id']], 'AUTHOR_ID': '173'}],
                   raw=True)
    else:
        flag = False
        id = dct['id']
        task = b.get_all('task.commentitem.getlist', {'ID': id})
        for comment in task:
            if '[USER=333]' in comment['POST_MESSAGE']:
                flag = True
        if flag is False:
            b.call('tasks.task.update', {'taskId': id, 'fields': {'STAGE_ID': '1117'}})
        else:
            task_name = dct['task_title'].split()
            if task_name[0] not in ['СВ:', 'СВ']:
                return
            task_date = task_name[-2:]
            main_task = b.get_all('tasks.task.list', {
                'filter': {
                    'TITLE': f"Сервисный выезд {dct['task_responsible']} {task_date[0]} {task_date[1]}"
                }
            })
            if not main_task:
                deadline = (datetime.strptime(dct['deadline'], '%d.%m.%Y %H:%M:%S'))
                deadline = f'{int_to_month[deadline.month]} {deadline.year}'
                main_task = b.get_all('tasks.task.list', {
                    'filter': {
                        'TITLE': f"Сервисный выезд (квартал) {dct['task_responsible']} {task_date[0]} {task_date[1]} - {deadline}"
                    }
                })
            main_task_id = main_task[0]['id']
            check_list = b.call('task.checklistitem.getlist', [main_task_id], raw=True)['result']
            task_row = list(filter(lambda x: dct['id'] in x['TITLE'], check_list))
            b.call('task.checklistitem.complete', [task_row[0]['PARENT_ID'], task_row[0]['ID']], raw=True)

