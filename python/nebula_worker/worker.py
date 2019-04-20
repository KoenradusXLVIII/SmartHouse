# Public Packages
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar
import pandas as pd

# Private Packages
# Import Nebula SQLAlchemy database structure
from nebula_alchemy.base import Session
from nebula_alchemy.interval import Interval
from nebula_alchemy.schedule import Schedule
from nebula_alchemy.algorithm import Algorithm
from nebula_alchemy.sensor import Sensor
from nebula_alchemy.quantity import Quantity
from nebula_alchemy.node import Node
from nebula_alchemy.user import User
from nebula_alchemy.meas import Meas
from nebula_alchemy.processed import Processed

from algorithms import *

# Algorithm map
algorithm_map = {
    'sum': sum,
    'min': min,
    'mean': mean,
    'max': max
}

def process(date_from, date_to, interval_name):
    schedule = session.query(Schedule) \
        .join(Interval) \
        .join(Sensor, Schedule.sensors) \
        .filter(Interval.name == interval_name)

    for event in schedule:
        for sensor in event.sensors:
            data_query = session.query(Meas) \
                .join(Sensor) \
                .filter(Sensor.id == sensor.id) \
                .filter(Meas.timestamp >= date_from, Meas.timestamp <= date_to) \
                .statement
            df = pd.read_sql(data_query, session.bind)
            value = algorithm_map[event.algorithm.name](df['value'])
            update = session.query(Processed) \
                .filter(Processed.sensor_id == sensor.id) \
                .filter(Processed.timestamp >= date_from, Processed.timestamp <= date_to) \
                .filter(Processed.algorithm_id == event.algorithm.id) \
                .filter(Processed.interval_id == event.interval_id) \
                .first()
            if update:
                print('..Update sensor %d - %s / %s %s / %.2f' % (
                sensor.id, sensor.name, event.interval.name, event.algorithm.name, value))
                update_entry = session.query(Processed) \
                    .filter(Processed.sensor_id == sensor.id) \
                    .filter(Processed.timestamp >= date_from, Processed.timestamp <= date_to) \
                    .filter(Processed.algorithm_id == event.algorithm.id) \
                    .filter(Processed.interval_id == event.interval_id) \
                    .update({'timestamp': date_from, 'value': value})
            else:
                print('..Write sensor %d - %s / %s %s / %.2f' % (
                    sensor.id, sensor.name, event.interval.name, event.algorithm.name, value))
                processed_value = Processed(date_from, sensor, value, event.interval, event.algorithm)
                session.add(processed_value)

# Start a session
session = Session()

# Run daily queries
date_from = datetime(datetime.today().year, datetime.today().month, datetime.today().day, 0, 0, 0) + relativedelta(days=-1)
date_to = datetime(datetime.today().year, datetime.today().month, datetime.today().day, 23, 59, 59) + relativedelta(days=-1)
process(date_from, date_to, 'Daily')

# Run weekly queries
if calendar.day_name[datetime.today().weekday()] == 'Monday':
    date_from = datetime(datetime.today().year, datetime.today().month, datetime.today().day, 0, 0, 0) + \
        relativedelta(weeks=-1)
    date_to = datetime(datetime.today().year, datetime.today().month, datetime.today().day, 23, 59, 59) + \
        relativedelta(days=-1)
    process(date_from, date_to, 'Weekly')

# Run monthly queries
if datetime.today().day == 1:
    date_from = datetime(datetime.today().year, datetime.today().month, datetime.today().day, 0, 0, 0) + \
        relativedelta(months=-1)
    date_to = datetime(datetime.today().year, datetime.today().month, datetime.today().day, 23, 59, 59) + \
        relativedelta(days=-1)
    process(date_from, date_to, 'Monthly')

# Run yearly queries
if datetime.today().day == 1 and calendar.month_name[datetime.today().month] == 'January':
    date_from = datetime(datetime.today().year, datetime.today().month, datetime.today().day, 0, 0, 0) + \
        relativedelta(years=-1)
    date_to = datetime(datetime.today().year, datetime.today().month, datetime.today().day, 23, 59, 59) + \
        relativedelta(days=-1)
    process(date_from, date_to, 'Yearly')

# Commit and close session
session.commit()
session.close()
