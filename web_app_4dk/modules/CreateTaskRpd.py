from datetime import datetime
from datetime import timedelta

from fast_bitrix24 import Bitrix
'''
from web_app_4dk.modules.authentication import authentication

# Считывание файла authentication.txt

webhook = authentication('Bitrix')
b = Bitrix(webhook)
'''

def create_task_rpd():
    months = {
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
        12: 'Декабрь',
    }
    current_month = months[datetime.now().month]
    


create_task_rpd()