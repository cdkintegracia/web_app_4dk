import requests

from web_app_4dk.chat_bot_routes.ChatBotTools import Message
from web_app_4dk.chat_bot_routes.SendMessage import bot_send_message


def message_add_handler(req):
    message = Message(req)
    random_quote = requests.post(url='http://api.forismatic.com/api/1.0/?method=getQuote&&format=json&lang=ru').json()['quoteText']
    bot_send_message({'dialog_id': message.from_user_id, 'message': random_quote})
