from fast_bitrix24 import Bitrix
import openpyxl

from web_app_4dk.modules.authentication import authentication
from web_app_4dk.tools import send_bitrix_request


b = Bitrix(authentication('Bitrix'))

documents_delivery = {
        '69': '1581',
        '71': '1583',
        '': '',
        None: '',
    }
'''
guids = {
    '14b2e004-bb25-11e8-80c1-0050569065b7': '227',
    '4dbac4d4-cd86-11e9-80c7-ac1f6b6226d7': '241',
    '9e32e962-d2e6-11e9-80c7-ac1f6b6226d7': '193',
    '87391ffe-e4e8-11e9-80c7-ac1f6b6226d7': '215',
    'f929adea-518f-11ea-80ca-ac1f6b6226d7': '137',
    '564c1c34-636b-11ea-80cd-ac1f6b6226d7': '119',
    '033c43b1-6758-11ea-80cd-ac1f6b6226d7': '223',
    '4ada188c-833b-11ec-80d2-ac1f6b6226d7': '171',
    '2cf97587-d10d-11ec-80d5-ac1f6b6226d6': '233',
    '0e669e79-84f5-11ed-80d9-ac1f6b6226d7': '393',
    'fb427d8c-8ffd-11ed-80d9-ac1f6b6226d7': '403',
    'f0e2e7a4-900d-11ed-80d9-ac1f6b6226d7': '405',
    'de82327c-a206-11ed-80da-ac1f6b6226d6': '419',
    'a8e7c9b0-ab85-11ed-80da-ac1f6b6226d6': '427',
    '7ef3e859-b0f5-11ed-80dc-ac1f6b6226d7': '433',
    '81837adb-b673-11ed-80dc-ac1f6b6226d7': '435',
    '9660c0f1-cc6e-11ed-80dc-ac1f6b6226d7': '445',
    '6539a686-09c8-11ee-80dc-ac1f6b6226d7': '503',
    '92f12ee3-0e74-11ee-80dd-ac1f6b6226d7': '507',
    '168d18ee-f788-11ec-8a48-fa163e21d4b7': '311',
    '8d13d1ac-c922-11e6-8a6d-aa3d71163f04': '157',
    '8d13d1b4-c922-11e6-8a6d-aa3d71163f04': '161',
    '8d13d1b9-c922-11e6-8a6d-aa3d71163f04': '191',
    '8d13d1bd-c922-11e6-8a6d-aa3d71163f04': '179',
    '8d13d1cc-c922-11e6-8a6d-aa3d71163f04': '159',
    '8d13d1d3-c922-11e6-8a6d-aa3d71163f04': '187',
    '8d13d1e7-c922-11e6-8a6d-aa3d71163f04': '175',
    '8b6ec06d-c925-11e6-8a6d-aa3d71163f04': '229',
    '8b6ec084-c925-11e6-8a6d-aa3d71163f04': '129',
    '8b6ec087-c925-11e6-8a6d-aa3d71163f04': '169',
    '8b6ec088-c925-11e6-8a6d-aa3d71163f04': '185',
    '8b6ec0cc-c925-11e6-8a6d-aa3d71163f04': '177',
    '4f4d8f95-c928-11e6-8a6d-aa3d71163f04': '181',
    '4f4d8fa4-c928-11e6-8a6d-aa3d71163f04': '291',
    '4f4d8faa-c928-11e6-8a6d-aa3d71163f04': '189',
    'fdf9b76b-c930-11e6-8a6d-aa3d71163f04': '125',
    'b8ec79f8-c933-11e6-8a6d-aa3d71163f04': '19',
    'b8ec7a00-c933-11e6-8a6d-aa3d71163f04': '165',
    'd8a90a2f-c942-11e6-8a6d-aa3d71163f04': '225',
    'd8a90a7a-c942-11e6-8a6d-aa3d71163f04': '221',
    'e10ace84-c942-11e6-8a6d-aa3d71163f04': '131',
    'e10aced1-c942-11e6-8a6d-aa3d71163f04': '127',
    'e718877f-c942-11e6-8a6d-aa3d71163f04': '133',
    '8eca2d5b-c943-11e6-8a6d-aa3d71163f04': '217',
    '9ef9e47e-c943-11e6-8a6d-aa3d71163f04': '91',    # Додина Наталия Леонидовна
    '75d2aca4-c944-11e6-8a6d-aa3d71163f04': '199',
    '46b5672a-d662-11e6-8afe-0050569f0c3a': '109',
    '49f9f5f2-d732-11e6-8afe-0050569f0c3a': '245',
    '7c651726-4872-11ed-8c00-fa163e21d4b7': '355',
    'e0677df2-dd6e-11e6-8e7c-0050569f0c3a': '183',
    'bcaceff1-de6d-11e6-8e7c-0050569f0c3a': '67',
    '1a4712d7-de6e-11e6-8e7c-0050569f0c3a': '117',
    'f525f596-4075-11ec-8fff-fa163e21d4b7': '1',
    '728a69aa-df20-11e7-90d9-0050569f0c3a': '163',
    'cc5c329e-f6c4-11e7-90d9-0050569f0c3a': '123',
    '28cbed37-00db-11e8-90d9-0050569f0c3a': '121',
    'a757bc9c-29d0-11ed-983e-fa163e21d4b7': '339',
    '61eaeb8a-dcf3-11ed-9842-fa163e21d4b7': '471',
    '4bc8c99a-5104-4056-a8ef-8d8a0e041c57': '153',
    '1999f7de-c943-11e6-8a6d-aa3d71163f04': '135',
}
'''

def fill_act_document_smart_process(req):
    element_info = send_bitrix_request('crm.item.get', {
        'entityTypeId': '161',
        'id': req['element_id'],
    })['item']
    company_info = send_bitrix_request('crm.company.list', {
        'select': ['*', 'UF_*'],
        'filter': {
            'UF_CRM_1656070716': element_info['ufCrm41_1689103279']
        }
    })[0]
    update_fields = dict()
    update_fields['companyId'] = company_info['ID']
    update_fields['ufCrm41_1689862848017'] = documents_delivery[company_info['UF_CRM_1638093692254']]
    update_fields['observers'] = company_info['ASSIGNED_BY_ID']
    update_fields['assignedById'] = '91'
    if element_info['ufCrm41_1690283806']:
        user_b24 = send_bitrix_request('user.get', {
            'filter': {
                'UF_USR_1690373869887': element_info['ufCrm41_1690283806']
            }
        })
        if user_b24:
            update_fields['assignedById'] = user_b24[0]['ID']
    send_bitrix_request('crm.item.update', {
        'entityTypeId': '161',
        'id': req['element_id'],
        'fields': update_fields
    })
