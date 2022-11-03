from fast_bitrix24 import Bitrix

b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')

task = b.get_all('tasks.task.get', {'taskId': '62745'})

print(task)