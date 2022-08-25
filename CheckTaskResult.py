from fast_bitrix24 import Bitrix
from authentication import authentication

# Считывание файла authentication.txt

webhook = authentication('Bitrix')
b = Bitrix(webhook)


def check_task_result(dct):
    print(dct)