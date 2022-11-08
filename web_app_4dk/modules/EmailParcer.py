"""
https://habr.com/ru/post/688784/
"""

import imaplib
import email
from email.header import decode_header
import base64
from bs4 import BeautifulSoup
import re


mail_pass = "hGrWQhkxdPkpxTvz6TYW"
username = "korpovmoxem@mail.ru"
imap_server = "imap.mail.ru"
imap = imaplib.IMAP4_SSL(imap_server)
imap.login(username, mail_pass)
imap.select("INBOX")
unseen_mails = imap.search(None, "UNSEEN")
if unseen_mails[0] == 'OK':
    unseen_mail_numbers = [x.decode('utf-8') for x in unseen_mails[1]][0].split(' ')
    if unseen_mail_numbers:

        # Итератор по порядковым номерам писем
        for unseen_mail_number in unseen_mail_numbers:
            if unseen_mail_number:
                res, msg = imap.fetch(unseen_mail_number, '(RFC822)')
                if res == 'OK':
                    mail_info = email.message_from_bytes(msg[0][1])

                    # Отправитель письма
                    mail_from = mail_info['From']

                    # Тема письма
                    mail_header = 'Без темы'
                    if mail_info['Subject']:
                        if '=?' in mail_info['Subject'] and '?=' in mail_info['Subject']:
                            mail_header = decode_header(mail_info['Subject'])[0][0].decode()
                        else:
                            mail_header = mail_info['Subject']

                    # Текст письма \ вложения
                    mail_text = ''
                    if mail_info.is_multipart():
                        payload = mail_info.get_payload()
                        for part in mail_info.walk():
                            if part.get_content_maintype() == 'text' and part.get_content_subtype() == 'plain':
                                mail_text += f"{base64.b64decode(part.get_payload()).decode()}\n\n"
                            if part.get_content_disposition() == 'attachment':
                                pass
                    else:
                        mail_info_text = mail_info.get_payload()
                        mail_text = BeautifulSoup(mail_info_text, "html.parser").text





