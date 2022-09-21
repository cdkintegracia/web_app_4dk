from fast_bitrix24 import Bitrix
import gspread
import dateutil.parser

from web_app_4dk.authentication import authentication

webhook = authentication('Bitrix')
b = Bitrix(webhook)


def write_to_sheet(data: list):
    """
    Запись данных в Google Sheet
    :param data: Данные о событии
    :return:
    """
    access = gspread.service_account(f"/root/credentials/bitrix24-data-studio-2278c7bfb1a7.json")
    spreadsheet = access.open('bitrix_data')
    worksheet = spreadsheet.worksheet('user_statistics')
    worksheet.insert_row(data, index=2)


def time_handler(time: str) -> str:
    """
    Форматирование времени
    :param time: время в формате '2022-09-21T14:30:13+03:00'
    :return: дата в формате '01.01.2021'
    """
    time = dateutil.parser.isoparse(time)
    message_time = f"{time.day}.{time.month}.{time.year}"
    return message_time


def add_call(req: dict):
    """
    Фильтр звонка по коду ошибки, получение имени и фамилии сотрудника
    :param req: request.form
    :return:
    """
    if req['data[CALL_FAILED_CODE]'] == '200':
        return
    user_info = b.get_all('user.get', {'filter': {'ID': req['data[PORTAL_USER_ID]']}})
    data_to_write = [req['event'],
            f"{user_info['NAME']} {user_info['LAST_NAME']}",
            time_handler(req['CALL_START_DATE']),
            req['data[CALL_TYPE]']]

    write_to_sheet(data_to_write)


def add_mail(req: dict):
    pass


def update_user_statistics(req: dict):
    """
    Вызывает нужную функция для переданного типа события
    :param req: request.form
    :return:
    """
    funcs = {
        'ONVOXIMPLANTCALLEND': add_call,
    }
    funcs[req['event']](req)




if __name__ == '__main__':
    update_user_statistics()





