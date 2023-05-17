import requests

from web_app_4dk.modules.authentication import authentication
from web_app_4dk.chat_bot.SendMessage import bot_send_message


def command_add_handler(message):
    data = {
        'COMMAND_ID': '39',
        'MESSAGE_ID': message.message_id,
        'MESSAGE': 'Клавиатура',
    },

    r = requests.post(url=f'{authentication("Chat-bot")}imbot.command.answer', json=data)
    bot_send_message({'dialog_id': '311', 'message': message.message_id})