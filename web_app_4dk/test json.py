import json

dct = {
'event_type': 'line',
'event_source': 'line',
'message_type': 80,
'author_id': '2d1dd0bd-fa0f-11e4-80d2-0025904f970d',
'treatment_id': 'f2c5e524-ae33-4802-8164-5238df02b291',
'line_id': '2eff464d-fada-11e4-80d4-0025904f970f',
'message_id': 'a353ee88-99ca-4256-9fe6-6cc9c8acd890',
'message_time': '2022-09-13T07:04:35.797329448Z',
'user_id': '0ed32a0a-2a2e-4d4b-98db-0778f0877ae2',
'text': '<buhphone><name>2d1dd0bd-fa0f-11e4-80d2-0025904f970d</name></buhphone>',
}

'''
with open('connect.json', 'a') as file:
    json.dump(dct, file)
'''

with open('connect.json', 'r') as file:
    print(json.load(file))