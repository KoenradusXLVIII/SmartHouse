import schedule
import time
import requests
from logger import client

# Scheduler reference examples
#  schedule.every(5).to(10).days.do(job)
#  schedule.every().monday.do(job)
#  schedule.every().wednesday.at("13:15").do(job)
#  schedule.every(10).seconds.do(job)
#  schedule.every().hour.do(job)

# Set up logger
log_client = client('Python scheduler','info')

# Define jobs
def reset_rain_meter():
    r = requests.get('http://192.168.1.112/rain/0')
    log_client.info('Rain meter reset to 0')

# Schedule jobs
schedule.every().day.at("00:00").do(reset_rain_meter)

# Run scheduler
while True:
    schedule.run_pending()
    time.sleep(1)