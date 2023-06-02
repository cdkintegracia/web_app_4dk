class Message:

    def __init__(self, request_data):
        self.from_user_id = request_data['data[PARAMS][FROM_USER_ID]']
        self.text = request_data['data[PARAMS][MESSAGE]'] if 'data[PARAMS][MESSAGE]' in request_data else None
        self.message_type = request_data['data[PARAMS][MESSAGE_TYPE]']
        self.template_id = request_data['data[PARAMS][TEMPLATE_ID]']
        self.to_user_id = request_data['data[PARAMS][TO_USER_ID]']
        self.event = request_data['event']
        self.message_id = request_data['data[PARAMS][MESSAGE_ID]']

        file_attr = None
        for attr in request_data:
            if 'data[PARAMS][FILES]' in attr:
                file_attr = attr
                file_attr = file_attr[file_attr.index('[FILES]') + 8:]
                break

        if file_attr:
            self.file_id = file_attr[:file_attr.index(']')]
            self.file_name = request_data[f'data[PARAMS][FILES][{self.file_id}][name]']
            self.file_extension = request_data[f'data[PARAMS][FILES][{self.file_id}][extension]']
            self.file_url_download = 'https://vc4dk.bitrix24.ru' + request_data[f'data[PARAMS][FILES][{self.file_id}][urlDownload]']
        else:
            self.file_id = None
            self.file_name = None
            self.file_extension = None
            self.file_url_download = None
