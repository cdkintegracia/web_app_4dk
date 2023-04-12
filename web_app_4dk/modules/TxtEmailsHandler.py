from fast_bitrix24 import Bitrix
from email_validate import validate
import openpyxl
from datetime import datetime

from authentication import authentication


'''
b = Bitrix(authentication('Bitrix'))

with open('Контакты 3.txt', encoding="utf8") as contacts_file_2:
    contacts_list_2 = list(map(lambda x: x.replace('\n', ''), contacts_file_2.readlines()))

with open('unique_emails.txt') as contacts_file_1:
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
with open('unique_emails_2.txt', 'w') as new_file:
    for row in unique_emails:
        new_file.write(f"{row}\n")
'''
emails_list = []
with open('unique_emails_2.txt', 'r') as file:
    for i in file:
        emails_list.append(i.strip('\n'))

validated_emails = []
count = 0
for email in emails_list:
    try:
        count += 1
        print(count, len(emails_list))
        email_validate = validate(
            email_address=email,
            check_blacklist=False,
            check_dns=False,
            #check_smtp=False,
            smtp_timeout=60
        )
        if email_validate:
            validated_emails.append(email)
    except:
        pass
with open('validated_emails.txt', 'w') as file:
    for email in validated_emails:
        file.write(f'{email}\n')


