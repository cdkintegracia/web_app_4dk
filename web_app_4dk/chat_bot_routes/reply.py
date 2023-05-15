import requests


json = {
    'BOT_ID': '495',
    'CLIEND_ID': 'vv58t6uleb5nyr3li47xp2mj5r3n46tb',
    'DIALOG_ID': '311',
    'MESSAGE': 'sup'
}
r = requests.post('https://vc4dk.bitrix24.ru/rest/311/5we272zatpjbdqsl/imbot.message.add.json?BOT_ID=495&CLIENT_ID=vv58t6uleb5nyr3li47xp2mj5r3n46tb&DIALOG_ID=1&MESSAGE=Привет! Я чат-бот!')

