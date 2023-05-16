from web_app_4dk.chat_bot_routes.ChatBotTools import Message


def message_add_handler(req):
    message = Message(req)
    print(message)