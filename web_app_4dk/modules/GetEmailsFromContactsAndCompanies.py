from fast_bitrix24 import Bitrix
from time import sleep

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))

deals = b.get_all('crm.deal.list', {
    'select': ['COMPANY_ID'],
    'filter': {
        'TYPE_ID': ['UC_2B0CK2', 'UC_86JXH1', 'UC_WUGAZ7'],
    },
})

spark_companies = list(map(lambda x: x['COMPANY_ID'], deals))
companies = b.get_all('crm.company.list', {
    'select': ['EMAIL'],
    'filter': {
    '!ID': spark_companies
}})
emails = []
company_emails = list(map(lambda x: x['EMAIL'] if 'EMAIL' in x else [], companies))
company_emails = list(filter(None, company_emails))
for company_email in company_emails:
    for email in company_email:
        emails.append(email['VALUE'])

contacts = []
companies_id = list(map(lambda x: x['ID'], companies))

for index, i in enumerate(companies_id):
    print(index)
    company_contacts = b.get_all('crm.company.contact.items.get', {'id': i})
    sleep(1)
    if company_contacts:
        company_contacts = list(map(lambda x: x['CONTACT_ID'], company_contacts))
        contacts.extend(company_contacts)

contacts_info = b.get_all('crm.contact.list', {
    'select': ['EMAIL'],
    'filter': {
        'ID': contacts
    }
})
contact_emails = list(filter(None, company_emails))
for contact_email in contact_emails:
    for email in contact_email:
        emails.append(email['VALUE'])

emails = set(emails)

with open('emails.txt', 'a') as file:
    for email in emails:
        file.write(f'{email}\n')


