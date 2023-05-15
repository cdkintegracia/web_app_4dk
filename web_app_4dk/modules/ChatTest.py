from fast_bitrix24 import Bitrix

from authentication import authentication


b = Bitrix(authentication('Bitrix'))


b.call('im.message.add', {
    'DIALOG_ID': '311',
    'MESSAGE': 'sup',
    'SYSTEM': 'N',

})


b.call('im.message.command', {

})