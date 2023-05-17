class Message:

    def __init__(self, request_data):
        self.from_user_id = request_data['data[PARAMS][FROM_USER_ID]']
        self.text = request_data['data[PARAMS][MESSAGE]']
        self.message_type = request_data['data[PARAMS][MESSAGE_TYPE]']
        self.template_id = request_data['data[PARAMS][TEMPLATE_ID]']
        self.to_user_id = request_data['data[PARAMS][TO_USER_ID]']
        self.event = request_data['event']
        self.message_id = request_data['data[PARAMS][MESSAGE_ID]']
