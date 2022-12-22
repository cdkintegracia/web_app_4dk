from fast_bitrix24 import Bitrix
import openpyxl


b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')


def read_xlsx(filename):
    workbook = openpyxl.load_workbook(filename)
    worksheet = workbook.active
    max_rows = worksheet.max_row
    max_columns = worksheet.max_column
    data = []
    titles = {}
    for row in range(1, max_rows + 1):
        for column in range(1, max_columns + 1):
            cell_value = worksheet.cell(row, column).value
            print(cell_value)
            exit()


def edo_info_handler():
    read_xlsx()