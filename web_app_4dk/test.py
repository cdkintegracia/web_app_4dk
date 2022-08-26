from fast_bitrix24 import Bitrix

from web_app_4dk.authentication import authentication

# Считывание файла authentication.txt

webhook = authentication('Bitrix')
b = Bitrix(webhook)

t = b.call('tasks.task.start', {'taskId': '50719'})
print(t)
