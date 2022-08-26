from fast_bitrix24 import Bitrix


webhook = 'https://vc4dk.bitrix24.ru/rest/311/r1oftpfibric5qym/'
b = Bitrix(webhook)

t = b.call('tasks.task.renew', {'taskId': '50699'})
print(t)
