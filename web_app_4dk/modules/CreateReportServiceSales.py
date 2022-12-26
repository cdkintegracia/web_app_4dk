from fast_bitrix24 import Bitrix
import openpyxl


b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')


def read_deals_from_xlsx(filename):
    workbook = openpyxl.load_workbook(filename)
