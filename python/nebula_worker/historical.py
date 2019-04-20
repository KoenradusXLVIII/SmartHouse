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
            if not df.empty:
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
start_date = datetime(2018,12,28,0,0,0)
while start_date <= datetime.today():
    print('Processing data for %s' % start_date.strftime('%d-%m-%Y'))
    date_from = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0) + relativedelta(days=-1)
    date_to = datetime(start_date.year, start_date.month, start_date.day, 23, 59, 59) + relativedelta(days=-1)
    process(date_from, date_to, 'Daily')

    # Run weekly queries
    if calendar.day_name[start_date.weekday()] == 'Monday':
        date_from = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0) + \
            relativedelta(weeks=-1)
        date_to = datetime(start_date.year, start_date.month, start_date.day, 23, 59, 59) + \
            relativedelta(days=-1)
        process(date_from, date_to, 'Weekly')

    # Run monthly queries
    if start_date.day == 1:
        date_from = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0) + \
            relativedelta(months=-1)
        date_to = datetime(start_date.year, start_date.month, start_date.day, 23, 59, 59) + \
            relativedelta(days=-1)
        process(date_from, date_to, 'Monthly')

    # Run yearly queries
    if start_date.day == 1 and calendar.month_name[start_date.month] == 'January':
        date_from = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0) + \
            relativedelta(years=-1)
        date_to = datetime(start_date.year, start_date.month, start_date.day, 23, 59, 59) + \
            relativedelta(days=-1)
        process(date_from, date_to, 'Yearly')

    # Next date
    session.commit()
    start_date = start_date + relativedelta(days=+1)

# Commit and close session

session.close()
