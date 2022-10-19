from fast_bitrix24 import Bitrix
from requests.auth import HTTPBasicAuth  # or HTTPDigestAuth, or OAuth1, etc.
from requests import Session
from zeep import Client
from zeep.transports import Transport
import openpyxl


b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')

# Клиент для XML запроса
session = Session()
session.auth = HTTPBasicAuth('bitrix', 'SekXd4')
client = Client('https://cus.buhphone.com/cus/ws/PartnerWebAPI2?wsdl',
                transport=Transport(session=session))


# Получение списка сотрудников компании-клиента
company_users = client.service.ClientUserRead('Params')

# Получение списка компаний-клиентов
companies = client.service.ClientRead('Params')

false_names = []
true_names = []
counter = 0
con_id = []
for client in company_users[1]['Value']['row']:
    flag = False
    client_name = f"{client['Value'][5]} {client['Value'][4]}"
    for company in companies[1]['Value']['row']:
        if company['Value'][0] == client['Value'][1]:
            bitrix_info = b.get_all('crm.company.list', {'filter': {'UF_CRM_1656070716': company['Value'][4]}})
            if not bitrix_info:
                continue
            bitrix_company = bitrix_info[0]
            bitrix_clients = b.get_all('crm.company.contact.items.get', {'id': bitrix_company['ID']})
            for bitrix_client in bitrix_clients:
                bitrix_client_info = b.get_all('crm.contact.get', {'id': bitrix_client['CONTACT_ID']})
                bitrix_client_name = f"{bitrix_client_info['LAST_NAME']} {bitrix_client_info['NAME']}"
                if client_name == bitrix_client_name:
                    flag = True
                    break
                elif bitrix_client_info['NAME'] is not None and client['Value'][4] is not None and bitrix_client_info['NAME'].strip(' ') == client['Value'][4].strip(' '):
                    count = 0
                    for check_uniq_name in bitrix_clients:
                        check_info = b.get_all('crm.contact.get', {'id': check_uniq_name['CONTACT_ID']})
                        check_name = f"{check_info['LAST_NAME']} {check_info['NAME']}"
                        if check_info['NAME'].strip() == bitrix_client_info['NAME'].strip():
                            count += 1
                    if count == 1:
                        flag = True
                        break

    if flag is False:
        if [bitrix_company['TITLE'], client_name, f'https://vc4dk.bitrix24.ru/crm/company/details/{bitrix_company["ID"]}/'] not in false_names:
            false_names.append([bitrix_company['TITLE'], client_name, f'https://vc4dk.bitrix24.ru/crm/company/details/{bitrix_company["ID"]}/'])
    else:
        if [bitrix_company['TITLE'], client_name, f'https://vc4dk.bitrix24.ru/crm/company/details/{bitrix_company["ID"]}/'] not in true_names:
            true_names.append([bitrix_company['TITLE'], client_name, f'https://vc4dk.bitrix24.ru/crm/company/details/{bitrix_company["ID"]}/'])
    counter += 1
    print(f"{counter} | {len(company_users[1]['Value']['row'])}")


new_list = []
good_list = []
for i in false_names:
    if i not in new_list:
        new_list.append(i)

for i in true_names:
    b.call('crm.contact.update', {'ID': i[-1], 'fields': {'UF_CRM_1666098408': '1'}})


workbook = openpyxl.load_workbook('false_names.xlsx')
worklist = workbook.active
worklist.append(['Компания', 'Имя в коннекте', 'Имя в Битриксе', 'Ссылка'])
for name in new_list:
    worklist.append(name)
workbook.save('false_names.xlsx')

workbook = openpyxl.load_workbook('true_names.xlsx')
worklist = workbook.active
worklist.append(['Компания', 'Имя в коннекте', 'Имя в Битриксе', 'Ссылка'])
for name in true_names:
    worklist.append(name)
workbook.save('true_names.xlsx')
