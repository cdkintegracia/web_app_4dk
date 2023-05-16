import requests

from web_app_4dk.modules.authentication import authentication


def bot_send_message(req: dict) -> None:
    """
    :param req: {
    dialog_id: числовое значение id пользователя или id чата в формате <chat13>,
    message: текст сообщения,
    }
    :return:
    """


    data = {
        'BOT_ID': '495',
        'CLIENT_ID': 'vv58t6uleb5nyr3li47xp2mj5r3n46tb',
        'DIALOG_ID': req['dialog_id'][5:] if 'user' in req['dialog_id'] else req['dialog_id'],
        'MESSAGE': req['message'],
    }
    r = requests.post(url=f'{authentication("Chat-bot")}imbot.message.add', json=data)

