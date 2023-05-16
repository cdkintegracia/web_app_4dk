from web_app_4dk.chat_bot_routes.ChatBotTools import Message
from web_app_4dk.chat_bot_routes.SendMessage import bot_send_message


def message_add_handler(req):
    message = Message(req)
    bot_send_message({'dialog_id': message.from_user_id, 'message': message.text})
