from fast_bitrix24 import Bitrix
import gspread
from time import strftime


b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')


b.call('im.notify.personal.add', {'USER_ID': '311', 'MESSAGE': f"Сверка ИТС завершена\n"})
