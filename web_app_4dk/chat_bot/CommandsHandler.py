import requests


def command_add_handler(message):
    print(message.message_id)
    print(message.text)