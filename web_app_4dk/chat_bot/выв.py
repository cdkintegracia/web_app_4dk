import requests

'''
data = {
        'BOT_ID': '495',
        'CLIENT_ID': 'vv58t6uleb5nyr3li47xp2mj5r3n46tb',
        'COMMAND': 'commands',
        'COMMON': 'Y',
        'COMMAND_ID': '37',
        'LANG': ['RU', 'ENG'],
        'EVENT_COMMAND_ADD': 'http://141.8.195.67:5000/bitrix/chat_bot',
        'HIDDEN': 'N'
    }


r = requests.post(url=f'https://vc4dk.bitrix24.ru/rest/311/5we272zatpjbdqsl/imbot.command.register', json=data)
print(r.text)
'''
data = {
        'BOT_ID': '495',
        'CLIENT_ID': 'vv58t6uleb5nyr3li47xp2mj5r3n46tb',
        'COMMAND': 'commands',
        'COMMON': 'Y',
        'COMMAND_ID': '37',
        'LANG': ['RU', 'ENG'],
        'EVENT_COMMAND_ADD': 'http://141.8.195.67:5000/bitrix/chat_bot',
        'HIDDEN': 'N'
    }

data = {
        'BOT_ID': '495',
        'CLIENT_ID': 'vv58t6uleb5nyr3li47xp2mj5r3n46tb',
        'DIALOG_ID': '311',
        'MESSAGE': 'Клавиатура',
        'KEYBOARD': [{ "TEXT": "Bitrix24",
        "LINK": "http://bitrix24.com",
        "BG_COLOR": "#29619b",
        "TEXT_COLOR": "#fff",
        "DISPLAY": "LINE",
        }]
    }

r = requests.post(url=f'https://vc4dk.bitrix24.ru/rest/311/5we272zatpjbdqsl/imbot.message.add', json=data)
print(r.text)