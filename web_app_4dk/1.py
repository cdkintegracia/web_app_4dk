from fast_bitrix24 import Bitrix
import dateutil.parser
from datetime import timedelta
b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')

time = dateutil.parser.isoparse('2022-09-14T07:33:55.294499949Z')
time += timedelta(hours=3)
message_time = f"{time.hour}:{time.minute}:{time.second} {time.day}.{time.month}.{time.year}"
print(message_time)