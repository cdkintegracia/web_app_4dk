from fast_bitrix24 import Bitrix
import openpyxl

b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')


workbook = openpyxl.load_workbook('Отчет_Мегафон_07-12-2022_17_14_40_685685.xlsx')
worklist = workbook.active
max_rows = worklist.max_row
max_columns = worklist.max_column
megafon_data = []
titles = {}
reverse_titles = {}
for row in range(1, max_rows + 1):
    temp = {}
    for column in range(1, max_columns + 1):
        if row == 1:
            titles.setdefault(worklist.cell(row, column).value, column)
            reverse_titles.setdefault(column, worklist.cell(row, column).value)
        else:
            temp.setdefault(reverse_titles[column], worklist.cell(row, column).value)
    if temp:
        megafon_data.append(temp)

b24_elements = b.get_all()

