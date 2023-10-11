from fast_bitrix24 import Bitrix
import openpyxl

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))
names = [
    'Январь_2023',
    'Февраль_2023',
    'Март_2023',
    'Апрель_2023',
    'Май_2023',
    'Июнь_2023',
    'Июль_2023',
    'Август_2023',
    'Сентябрь_2023',
]

for name in names:
    file = openpyxl.load_workbook(f'C:\\Users\\Максим\\Documents\\GitHub\\web_app_4dk\\web_app_4dk\\deals_info_files\\{name}.xlsx')
    ws = file.active
    new_data = []
    for index, row in enumerate(ws.rows):
        print(index, name)
        temp = []
        if index != 0:
            for cell in row:
                temp.append(cell.value)
            try:
                deal_info = b.get_all('crm.deal.get', {
                    'ID':  temp[7],
                })
                temp.append(deal_info['UF_CRM_1640523562691'])
            except:
                continue
        else:
            for cell in row:
                temp.append(cell.value)
            temp.append('Регномер')
        new_data.append(temp)

    wl = openpyxl.Workbook()
    ws = wl.active
    for row in new_data:
        ws.append(row)
    wl.save(f'{name}_upd.xlsx')

