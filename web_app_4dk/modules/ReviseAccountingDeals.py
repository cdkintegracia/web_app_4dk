from fast_bitrix24 import Bitrix
import openpyxl


b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')


def read_report_file(filename: str) -> dict:
    workbook = openpyxl.load_workbook(filename)
    worksheet = workbook.active
    max_rows = worksheet.max_row
    max_cols = worksheet.max_column
    file_data = []
    titles = []
    for row in range(1, max_rows + 1):
        temp = {}
        for column in range(1, max_cols + 1):
            if row == 1:
                titles.append(str(worksheet.cell(row=row, column=column).value))
            else:
                temp.setdefault(titles[column - 1], worksheet.cell(row=row, column=column).value)
        if temp and temp['Наименование тарифа'] not in [
            'Информационно-технологическое сопровождение 1С',
            'Обслуживание учетной записи 1С в рамках ранее заключенного договора',
            'Промо (1 месяц бесплатно)',
            'Промо Кадровые решения (ФСС и ПФР)',
        ]:
            file_data.append(temp)
    titles.append('Расхождение')
    titles.append('Цена из Битрикса')
    titles.append('Цена')
    return {'titles': titles, 'data': file_data}


def revise_accounting_deals(filename='1.xlsx'):
    job_counter = 0
    file_data = read_report_file(filename)
    for file_line in file_data['data']:
        registration_data_list = file_line['Дата регистрации'].split('.')
        registration_data = f"{registration_data_list[2]}-{registration_data_list[1]}-{registration_data_list[0]}"
        company_info = b.get_all('crm.company.list', {
            'filter': {'UF_CRM_1656070716': file_line['ИНН абонента'],
                       'UF_CRM_1654682057': registration_data
                       }})
        if not company_info:
            file_line.setdefault('Расхождение', 'Нет ИНН')
            continue
        company_id = company_info[0]['ID']
        company_deals = b.get_all('crm.deal.list', {'filter': {'TYPE_ID': 'UC_O99QUW', 'COMPANY_ID': company_id}})
        if not company_deals:
            file_line.setdefault('Расхождение', 'Нет отчетности')
            continue
        company_deal = company_deals[0]
        if int(float(company_deal['OPPORTUNITY'])) < int(float(file_line['Цена'])):
            file_line.setdefault('Расхождение', 'Некорректная сумма')
        else:
            file_line.setdefault('Расхождение', 'Нет')
        price = file_line.pop('Цена')
        file_line.setdefault('Сумма из Битрикса', int(float(company_deal['OPPORTUNITY'])))
        file_line.setdefault('Цена', price)
        job_counter += 1
        print(f"{job_counter} | {len(file_data['data'])}")

    ind = 0
    for i in range(len(file_data['titles'])):
        if file_data['titles'][i] == 'Цена':
            ind = i
            break
    del file_data['titles'][ind]
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.append(file_data['titles'])
    for data in file_data['data']:
        worksheet.append(list(data.values()))
    workbook.save('result.xlsx')


revise_accounting_deals()











