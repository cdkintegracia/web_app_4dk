from authentication import authentication
from fast_bitrix24 import Bitrix
"""
call_types:
1 - входящий
2 - исходящий
"""

# Считывание файла authentication.txt

webhook = authentication('Bitrix')
b = Bitrix(webhook)

employee_numbers = [
    '+79991174816',     # Жанна Умалатова
    '+79991174814',     # Елена Коршакова
    '+79991174815',     # Екатерина Плотникова
    '+79991174818',     # Ольга Цветкова
    '+79991174812',     # Мария Боцула
    '+79522806626',     # МОЙ
]

def update_call_statistic(client_number, employee_number):
    if employee_number in employee_numbers:
        print('----------------------------------------------------')