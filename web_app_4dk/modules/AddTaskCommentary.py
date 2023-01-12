from fast_bitrix24 import Bitrix

from web_app_4dk.modules.authentication import authentication


b = Bitrix(authentication('Bitrix'))


def add_task_commentary(req):
    b.call('task.commentitem.add', [req['task_id'], {'POST_MESSAGE': req['address_field'], 'AUTHOR_ID': '173'}], raw=True)
