import base64

def authentication(key):
    """
    :param key: Сервис, для которого нужно вернуть аутентификацию.
    Данные должны находиться в файле "authentications.txt" в формате
    <СЕРВИС>: <КЛЮЧ>
    Например:
    Bitrix: fsdg5y344eqwdfsg4232g23
    Google Data Studio: dsgs425-data-studio-gdsfhrdd.json (название файла с доступом)
    Параметр "key" соответствует названию сервиса из файла
    :return: Возвращает необходимую для сервиса аутентификацию
    """

    # Считывание файла authentication.txt

    with open('/root/credentials/authentications.txt') as file:
    #with open('C:\\Users\\mok\\Documents\\GitHub\\web_app_4dk\\web_app_4dk\\authentications.txt') as file:
        lines = file.readlines()
        dct = {}
        for line in lines:
            lst = base64.b64decode(line).decode('utf-8').strip().split(': ')
            dct.setdefault(lst[0], lst[1].strip())


    return dct[key]
