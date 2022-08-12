import schedule
def ok():
    print('10101010101010101001100101010110')
schedule.every(10).minutes.do(ok)
while True:
    schedule.run_pending()