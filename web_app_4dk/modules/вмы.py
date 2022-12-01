from fast_bitrix24 import Bitrix

b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')

print(b.call('task.checklistitem.getlist', ['87149'], raw=True)['result'])