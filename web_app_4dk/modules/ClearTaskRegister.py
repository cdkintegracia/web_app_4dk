from datetime import datetime, timedelta

from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def clear_task_registry(req):
    filter_date = datetime.now() - timedelta(days=int(req['days']))
    start_date = datetime(day=1, month=2, year=datetime.now().year)
    counter = 0
    while start_date < filter_date:
        print(start_date.strftime('%d.%m.%Y'))
        end_date = start_date + timedelta(days=1)
        elements = b.get_all('lists.element.get', {
            'IBLOCK_TYPE_ID': 'lists',
            'IBLOCK_ID': '107',
            'filter': {
                '>=PROPERTY_505': start_date.strftime('%d.%m.%Y'),
                '<PROPERTY_505': end_date.strftime('%d.%m.%Y'),
            }
        })
        elements = filter(lambda x: 'PROPERTY_499' not in x, elements)
        for element in elements:
            b.call('lists.element.delete', {
                'IBLOCK_TYPE_ID': 'lists',
                'IBLOCK_ID': '107',
                'ELEMENT_ID': element['ID']
            })
            counter += 1
        start_date = start_date + timedelta(days=1)
        print(counter)

    b.call('im.notify.system.add', {
        'USER_ID': req['user_id'][5:],
        'MESSAGE': f'Очистка реестра задач завершена\n'
                   f'Удалено {counter} элементов'})
