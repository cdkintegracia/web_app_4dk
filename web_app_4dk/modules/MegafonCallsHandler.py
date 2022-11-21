from fast_bitrix24 import Bitrix
import openpyxl


b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')


def read_megafon_file():
    workbook = openpyxl.load_workbook('История внешних звонков 03-11-2022.xlsx')
    worksheet = workbook.active
    max_rows = worksheet.max_row
    max_columns = worksheet.max_column
    worksheet_titles = {}
    megafon_data = []

    for row in range(10, max_rows + 1):
        temp = []
        for column in range(1, max_columns + 1):
            if row == 10:
                worksheet_titles.setdefault(worksheet.cell(row, column).value, column - 1)
            else:
                temp.append(worksheet.cell(row, column).value)
        megafon_data.append(temp)


    b24_contacts = b.get_all('crm.contact.list')
    for contact in b24_contacts:
        print(contact['COMPANY_ID'])
    exit()
    b24_companies = b.get_all('crm.company.list')
    b24_deals = b.get_all('crm.deal.list', {
        'filter': {
            'CATEGORY_ID': '1',
            'STAGE_ID': [
                'C1:UC_0KJKTY',  # Счет сформирован
                'C1:UC_3J0IH6',  # Счет отправлен клиенту
                'C1:UC_KZSOR2',  # Нет оплаты
                'C1:UC_VQ5HJD',  # Ждём решения клиента
                'C1:NEW',  # Услуга активна
            ]}})



read_megafon_file()



