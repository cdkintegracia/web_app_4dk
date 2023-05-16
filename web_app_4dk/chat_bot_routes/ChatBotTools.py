class Message:

    def __init__(self, request_data):
        self.bot_code = request_data['data[BOT][495][BOT_CODE]']
        self.bot_id = request_data['data[BOT][495][BOT_ID]']
        self.from_user_id = request_data['data[PARAMS][FROM_USER_ID]']
        self.text = request_data['data[PARAMS][MESSAGE]']
        self.message_type = request_data['data[PARAMS][MESSAGE_TYPE]']
        self.url_id = request_data['data[PARAMS][PARAMS][URL_ID][0]']
        self.skip_url_index = request_data['data[PARAMS][SKIP_URL_INDEX]']
        self.template_id = request_data['data[PARAMS][TEMPLATE_ID]']
        self.to_user_id = request_data['data[PARAMS][TO_USER_ID]']
        self.event = request_data['ONIMBOTMESSAGEADD']