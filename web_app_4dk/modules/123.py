from fast_bitrix24 import Bitrix

b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')

b.call('task.elapseditem.add', ['66129', {'SECONDS': '122142141', 'USER_ID': '173'}], raw=True)