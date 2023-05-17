import requests

from web_app_4dk.modules.authentication import authentication
from web_app_4dk.chat_bot.SendMessage import bot_send_message


def command_add_handler(message):
    data = {
        'BOT_ID': '495',
        'CLIENT_ID': 'vv58t6uleb5nyr3li47xp2mj5r3n46tb',
        'DIALOG_ID': '311',
        'MESSAGE': 'Клавиатура',
        'COMMAND_ID': '39',
        'COMMAND': 'commands',
        'MESSAGE_ID': message.message_id,
        'KEYBOARD': [{
            "TEXT": "Bitrix24",
            "LINK": "http://bitrix24.com",
            "BG_COLOR": "#29619b",
            "TEXT_COLOR": "#fff",
            "DISPLAY": "LINE",
        }]
    },

    r = requests.post(url=f'{authentication("Chat-bot")}imbot.command.answer', json=data)
    bot_send_message({'dialog_id': '311', 'message': r.text})