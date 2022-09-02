from fast_bitrix24 import Bitrix
import gspread
from time import strftime
import base64

with open('authentications.txt', 'rb') as file:
    lines = file.readlines()
    dct = {}
    for line in lines:
        lst = base64.b64decode(line).decode('utf-8').strip().split(': ')
        dct.setdefault(lst[0], lst[1].strip())
    print(dct)
