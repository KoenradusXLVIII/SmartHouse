import schedule
import time
import logger
from jobs import reset_rain_meter, lights_out

# Set up logger
log_client = logger.Client('scheduler', 'info')

# Scheduler reference examples
#  schedule.every(5).to(10).days.do(job)
#  schedule.every().monday.do(job)
#  schedule.every().wednesday.at("13:15").do(job)
#  schedule.every(10).seconds.do(job)
#  schedule.every().hour.do(job)

# Schedule jobs
schedule.every().day.at("00:00").do(reset_rain_meter, log_client)
schedule.every().day.at("22:30").do(lights_out, log_client)

# Run scheduler
while True:
    schedule.run_pending()
    time.sleep(1)