from fast_bitrix24 import Bitrix
from requests.auth import HTTPBasicAuth  # or HTTPDigestAuth, or OAuth1, etc.
from requests import Session
from zeep import Client
from zeep.transports import Transport
import openpyxl



b = Bitrix()

# Клиент для XML запроса
session = Session()
session.auth = HTTPBasicAuth('bitrix', 'SekXd4')
client = Client('https://cus.buhphone.com/cus/ws/PartnerWebAPI2?wsdl',
                transport=Transport(session=session))


support_lines_clients = client.service.UserServiceLineRead('Params')
support_lines = client.service.ServiceLineKindRead('Params')
support_lines_dict = {}
for support_line in support_lines[1]['Value']['row']:
    if support_line['Value'][0] not in support_lines_dict:
        support_lines_dict.setdefault(support_line['Value'][0], support_line['Value'][2])


# Получение списка сотрудников компании-клиента
company_users = client.service.ClientUserRead('Params')

# Получение списка компаний-клиентов
companies = client.service.ClientRead('Params')

false_names = []
true_names = []
counter = 0
con_id = []
assigneds = {}
for client in company_users[1]['Value']['row']:
    flag = False
    client_name = f"{client['Value'][5]} {client['Value'][4]}"
    for company in companies[1]['Value']['row']:
        if company['Value'][0] == client['Value'][1]:
            bitrix_info = b.get_all('crm.company.list', {'filter': {'UF_CRM_1656070716': company['Value'][4]}})
            if not bitrix_info:
                continue
            bitrix_company = bitrix_info[0]
            if bitrix_company['ASSIGNED_BY_ID'] not in assigneds:
                assigned_info = b.get_all('user.get', {'id': bitrix_company['ASSIGNED_BY_ID']})[0]
                assigned_name = f"{assigned_info['LAST_NAME']} {assigned_info['NAME']}"
                assigneds.setdefault(bitrix_company['ASSIGNED_BY_ID'], assigned_name)
            assigned = assigneds[bitrix_company['ASSIGNED_BY_ID']]
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
    lines = 0
    for support_lines_client in support_lines_clients[1]['Value']['row']:
        line_id = support_lines_client['Value'][1]
        user_id = support_lines_client['Value'][0]
        if client['Value'][0] == user_id:
            for line in support_lines_dict:
                if line == line_id:
                    lines += 1


    if flag is False:
        if [bitrix_company['TITLE'], client_name, f'https://vc4dk.bitrix24.ru/crm/company/details/{bitrix_company["ID"]}/', lines, assigned] not in false_names:
            false_names.append([bitrix_company['TITLE'], client_name, f'https://vc4dk.bitrix24.ru/crm/company/details/{bitrix_company["ID"]}/', lines, assigned])
    else:
        if [bitrix_company['TITLE'], client_name, f'https://vc4dk.bitrix24.ru/crm/company/details/{bitrix_company["ID"]}/', lines, assigned] not in true_names:
            true_names.append([bitrix_company['TITLE'], client_name, f'https://vc4dk.bitrix24.ru/crm/company/details/{bitrix_company["ID"]}/', lines, assigned])
            b.call('crm.contact.update', {'ID': bitrix_client['CONTACT_ID'], 'fields': {'UF_CRM_1666098408': '1'}})
    counter += 1
    print(f"{counter} | {len(company_users[1]['Value']['row'])}")


new_list = []
good_list = []
for i in false_names:
    if i not in new_list:
        new_list.append(i)


workbook = openpyxl.Workbook()
worklist = workbook.active
worklist.append(['Компания', 'Имя в коннекте', 'Ссылка', 'Кол-во ЛК', 'Ответственный за компанию'])
for name in new_list:
    worklist.append(name)
workbook.save('false_names.xlsx')

workbook = openpyxl.Workbook()
worklist = workbook.active
worklist.append(['Компания', 'Имя в коннекте', 'Ссылка', 'Кол-во ЛК', 'Ответственный за компанию'])
for name in true_names:
    worklist.append(name)
workbook.save('true_names.xlsx')