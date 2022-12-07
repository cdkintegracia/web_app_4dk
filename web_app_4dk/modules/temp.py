import json
import dateutil.parser
from datetime import datetime, timedelta
import pytz
import io

logs = []
with io.open('connect_logs (3).txt', mode='r') as file:
    for line in file:
        logs.append(json.loads(line))

utc = pytz.UTC
logs = list(sorted(logs, key=lambda x: dateutil.parser.isoparse(x['message_time'])))
current_date = utc.localize(datetime.now() - timedelta(days=14))
filtred_logs = list(filter(lambda x: dateutil.parser.isoparse(x['message_time']) > current_date, logs))

with open('temp.txt', 'w') as file:
    for log in filtred_logs:
        json.dump(log, file, ensure_ascii=False)
        file.write('\n')
