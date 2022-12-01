from datetime import datetime, timedelta

year = '2022'
month = '12'

date_start = datetime.strptime(f'01-{month}-{year}', '%d-%m-%Y') - timedelta(days=1)
date_end = '01-' + datetime.strftime(date_start + timedelta(days=32), '%m-%Y')
print(date_end)