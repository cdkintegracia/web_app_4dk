from fast_bitrix24 import Bitrix
import time


b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')

tasks = b.get_all('tasks.task.list', {'filter': {'ID': '79757'}})
print(tasks[0]['durationFact'])
t = time.gmtime(int(tasks[0]['durationFact']))
print(time.strftime("%H:%M:%S", t))