from authentication import authentication
from fast_bitrix24 import Bitrix

# Считывание файла authentication.txt

webhook = authentication('Bitrix')
b = Bitrix(webhook)


def update_call_statistic(client_number, employee_number):
    pass