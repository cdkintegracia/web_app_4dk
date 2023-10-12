import csv

from fast_bitrix24 import Bitrix
import openpyxl

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))

file = openpyxl.load_workbook(f'C:\\Users\\Максим\\Documents\\GitHub\\web_app_4dk\\web_app_4dk\\deals_info_files\\Август_2023.xlsx')
ws = file.active
new_data = []

for index, row in enumerate(ws.rows):
    temp = []
    if index != 0:
        for cell in row:
            temp.append(cell.value)
    else:
        for cell in row:
            temp.append(cell.value)
    new_data.append(temp)

backup_data = []
with open(f'C:\\Users\\Максим\\Documents\\GitHub\\web_app_4dk\\web_app_4dk\\deals_info_files\\Сопровождение_31_08_2023.csv', encoding='UTF-8') as csv_file:
    csv_data = csv.reader(csv_file)
    for index, row in enumerate(csv_data):
        if index == 0:
            titles = row
        backup_data.append(dict(zip(titles, row)))

new_data[0].append('Дата проверки оплаты')
result = []
for index, row in enumerate(new_data):
    if index == 0:
        result.append(row)
        continue
    deal_id = row[7]
    deal_info = list(filter(lambda x: deal_id == x['ID'], backup_data))
    if deal_info:
        row.append(deal_info[0]['Дата проверки оплаты'])
    result.append(row)


wl = openpyxl.Workbook()
ws = wl.active
for row in result:
    ws.append(row)
wl.save(f'Август_2023.xlsx')

