import requests

from web_app_4dk.modules.authentication import authentication


def command_add_handler(message):
    data = {
        'COMMAND_ID': '39',
        'COMMAND': 'commands',
        'MESSAGE_ID': message.message_id,
        'MESSAGE': 'Отвечаю',
        'CLIENT_ID': 'vv58t6uleb5nyr3li47xp2mj5r3n46tb',
        'KEYBOARD': [
            {
                'TEXT': "Сверка по NewSub",
                'LINK': "http://141.8.195.67:5000/",
                'BG_COLOR': "#29619b",
                'TEXT_COLOR': "#fff",
                'DISPLAY': 'LINE'
            },
            {
                'TEXT': "Сверка по отчетности",
                'LINK': "http://141.8.195.67:5000/",
                'BG_COLOR': "#2a4c7c",
                'TEXT_COLOR': "#fff",
                'DISPLAY': 'LINE'
            }
        ]
    }
    r = requests.post(url=f'{authentication("Chat-bot")}imbot.command.answer', json=data)
    print(r.text)