from fast_bitrix24 import Bitrix

webhook = 'https://vc4dk.bitrix24.ru/rest/311/r1oftpfibric5qym/'
b = Bitrix(webhook)

t = b.get_all('tasks.task.list', {'params': {'WITH_RESULT_INFO': 'false'}, 'select': ['TITLE'], 'filter': {'ID': '50555'}})

print(t)