from fast_bitrix24 import Bitrix
import openpyxl


b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')


def read_megafon_file():
    workbook = openpyxl.load_workbook('История внешних звонков 03-11-2022.xlsx')
    worksheet = workbook.active
    rows = worksheet.max_row
    columns = worksheet.max_column
    worksheet_titles = {}

