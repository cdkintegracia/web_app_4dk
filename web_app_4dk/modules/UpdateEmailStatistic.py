from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


# Считывание файла authentication.txt

webhook = authentication('Bitrix')
b = Bitrix(webhook)


def update_email_statistic(activity_info: dict):
    """
    Запускается из UpdateUserStatistics

    :param activity_info: данные о деле, полученные через crm.activity.get
    :return:
    """
    print(activity_info)
    return
    b.call('im.notify.system.add', {
        'USER_ID': '311',
        'MESSAGE': activity_info})