import schedule
def ok():
    print('10101010101010101001100101010110')
schedule.every(1).minutes.do(ok)
while True:
    schedule.run_pending()