from fast_bitrix24 import Bitrix

try:
    from authentication import authentication
except ModuleNotFoundError:
    from web_app_4dk.modules.authentication import authentication


def service_task_quarterly(req):
    print(req)

