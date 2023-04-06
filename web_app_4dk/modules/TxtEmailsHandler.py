from fast_bitrix24 import Bitrix

from authentication import authentication


b = Bitrix(authentication('Bitrix'))

with open('Контакты 2.txt') as contacts_file_2:
    contacts_list_2 = list(map(lambda x: x.replace('\n', ''), contacts_file_2.readlines()))

with open('контакты.txt') as contacts_file_1:
    contacts_list_1 = list(map(lambda x: x.replace('\n', ''), contacts_file_1.readlines()))

contacts_list = contacts_list_1 + contacts_list_2
file_emails_list = list(filter(lambda x: 'gk4dk.ru' not in x, contacts_list))

b24_contacts_info = b.get_all('crm.contact.list', {'select': ['EMAIL']})
b24_contacts_info = list(filter(lambda x: 'EMAIL' in x, b24_contacts_info))
b24_contacts_emails = []
for info in b24_contacts_info:
    for email_info in info['EMAIL']:
        b24_contacts_emails.append(email_info['VALUE'])

b24_companies_info = b.get_all('crm.company.list', {'select': ['EMAIL']})
b24_companies_info = list(filter(lambda x: 'EMAIL' in x, b24_companies_info))
b24_companies_emails = []
for info in b24_companies_info:
    for email_info in info['EMAIL']:
        b24_companies_emails.append(email_info['VALUE'])


unique_emails = set(filter(lambda x: x not in b24_companies_emails and x not in b24_contacts_emails, file_emails_list))
with open('unique_emails.txt', 'w') as new_file:
    for row in unique_emails:
        new_file.write(f"{row}\n")


