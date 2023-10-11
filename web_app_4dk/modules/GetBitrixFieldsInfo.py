from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication
from web_app_4dk.chat_bot.SendMessage import bot_send_message


b = Bitrix(authentication('Bitrix'))


def get_bitrix_fields_info(req):
    crm_types = {
        '1': 'lead',
        '2': 'deal',
        '3': 'contact',
        '7': 'quote',
        '5': 'invoice',
    }
    fields_info = ''
    if req['crm_id'] in crm_types:
        fields = b.get_all(f'crm.{crm_types[req["crm_id"]]}.fields')
    else:
        fields = b.get_all('crm.item.fields', {
            'entityTypeId': req['crm_id']
        })['fields']
    for code in fields:
        if req['crm_id'] not in crm_types:
            field_title = fields[code]['title']
        else:
            field_title = fields[code]["title"] if 'listLabel' not in fields[code] else fields[code]['listLabel']
        if 'items' in fields[code]:
            temp_info = f'{code} {field_title} {fields[code]["type"]} '
            items_info = list()
            for item in fields[code]['items']:
                items_info.append(f'{item["ID"]}: {item["VALUE"]}')
            temp_info += f"[{', '.join(items_info)}]"
            fields_info += temp_info + '\n'
        else:
            fields_info += f'{code} {field_title} {fields[code]["type"]}\n'

    bot_send_message({'dialog_id': req['user_id'][5:], 'message': fields_info})