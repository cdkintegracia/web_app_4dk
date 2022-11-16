"""
https://habr.com/ru/post/688784/
"""

import imaplib
import email
from email.header import decode_header
import base64
from bs4 import BeautifulSoup

from fast_bitrix24 import Bitrix

b = Bitrix('https://vc4dk.bitrix24.ru/rest/311/wkq0a0mvsvfmoseo/')


def html_parser(mail_info):
    html_text = BeautifulSoup(mail_info, "html.parser").findAll()
    mail_text = ''
    for text in html_text:
        mail_text += f'{text.text}\n'
    return mail_text


def upload_file_to_bx24(filename: str, filecontent: str) -> str:
    bitrix_folder_id = '214745'
    upload_file = b.call('disk.folder.uploadfile', {
        'id': bitrix_folder_id,
        'data': {'NAME': filename},
        'fileContent': filecontent,
        'generateUniqueName': 'true'
    })
    return upload_file['ID']


def mail_parser():
    mail_pass = "Ru3rhv84ydvvC5PCecE4"
    username = "mok@gk4dk.ru"
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
                        if '=?' in mail_from and '?=' in mail_from:
                            mail_from_name = decode_header(mail_from)[0][0].decode()
                            mail_from_email = mail_from.split(' ')[1].strip('<>')
                            mail_from = f"{mail_from_name} {mail_from_email}"

                        # Тема письма
                        mail_header = 'Без темы'
                        if mail_info['Subject']:
                            if '=?' in mail_info['Subject'] and '?=' in mail_info['Subject']:
                                mail_header = decode_header(mail_info['Subject'])[0][0].decode()
                            else:
                                mail_header = mail_info['Subject']

                        # Текст письма \ вложения
                        mail_text = ''
                        mail_attachments = {}
                        if mail_info.is_multipart():
                            payload = mail_info.get_payload()
                            for part in mail_info.walk():

                                # Текст письма закодирован
                                if part.get_content_maintype() == 'text' and part.get_content_subtype() == 'plain':
                                    try:
                                        mail_text += f"{base64.b64decode(part.get_payload()).decode()}\n\n"
                                    except ValueError:
                                        mail_text += part.get_payload()

                                # Текст письма в html формате
                                elif part.get_content_maintype() == 'text' and part.get_content_subtype() == 'html':
                                    mail_text = html_parser(part.get_payload())

                                # Парсинг файлов
                                if part.get_content_disposition() == 'attachment':
                                    file_name = 'Файл'
                                    if '=?' in part.get_filename() and '?=' in part.get_filename():
                                        file_name = decode_header(part.get_filename())[0][0].decode()
                                    else:
                                        file_name = part.get_filename()
                                    mail_attachments[file_name] = part.get_payload()

                        else:
                            mail_text = html_parser(mail_info.get_payload())

                        mail_attachment_id_list = []
                        if mail_attachments:
                            for filename in mail_attachments:
                                file_id = upload_file_to_bx24(filename, mail_attachments[filename])
                                mail_attachment_id_list.append(f'n{file_id}')

                        b.call('tasks.task.add', {
                            'fields': {
                                'TITLE': f'Входящее письмо: {mail_header}',
                                'DESCRIPTION': f'От: {mail_from}\n'
                                               f'Тема: {mail_header}\n'
                                               f'Текст:\n'
                                               f'{mail_text}',
                                'CREATED_BY': '173',
                                'GROUP_ID': '13',
                                'RESPONSIBLE_ID': '173',
                                'UF_TASK_WEBDAV_FILES': mail_attachment_id_list,
                            }})


if __name__ == '__main__':
    mail_parser()







