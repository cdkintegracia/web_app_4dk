from web_app_4dk.chat_bot.ChatBotTools import Message
from web_app_4dk.chat_bot.MessageHandler import message_add_handler
from web_app_4dk.chat_bot.CommandsHandler import command_add_handler
from web_app_4dk.chat_bot.SendMessage import bot_send_message


def message_handler(req):
    events = {
        'ONIMBOTMESSAGEADD': message_add_handler,
        'ONIMCOMMANDADD': command_add_handler,
    }
    '''
    for i in req:
        bot_send_message({'dialog_id': '311', 'message': f'{i} {req[i]}'})
    '''

    if req['event'] in events:
        message = Message(req)
        bot_send_message({'dialog_id': '311', 'message': message.file_url_download})
        events[message.event](message)
