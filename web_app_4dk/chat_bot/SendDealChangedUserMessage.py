from web_app_4dk.chat_bot.SendMessage import bot_send_message


def send_deal_changed_user_message(req):
    bot_send_message({
        'dialog_id': '157',
        'message': f'Ответственным за сделку {req["deal_name"]} https://vc4dk.bitrix24.ru/crm/deal/details/{req["deal_id"]}/ был назначен {req["user_after"]} вместо {req["user_before"]}'
    })