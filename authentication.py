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

    with open('/root/autorun/authentications.txt') as file:
    #with open('authentications.txt') as file:
        lines = file.readlines()
        dct = {}
        for line in lines:
            lst = line.split(': ')
            dct.setdefault(lst[0], lst[1].strip())

    return dct[key]
