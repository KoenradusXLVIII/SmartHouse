# Public packages
import os
import yaml
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
from sqlalchemy import create_engine
from sqlalchemy.engine import url
import pandas as pd
import numpy as np

#Private packages
import nebula


def daily_sum(df_sensors):
    query = 'SELECT DATE(timestamp) as timestamp, sensors.id as sensor_id, meas.value FROM meas ' \
            'LEFT JOIN sensors ON meas.sensor_id = sensors.id WHERE sensors.id IN (%s) ' \
            'AND DATE(timestamp) = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY))' %\
            ", ".join(map(str, df_sensors['sensor_in_id']))
    df = pd.read_sql_query(query, con=engine)
    if not df.empty:
        nebula_client.info('Daily sum: %d values to process' % len(df.index))

        # Compute daily sum
        df_sum = df.groupby(['timestamp', 'sensor_id'], as_index=False).sum()
        df_sum['sensor_id'] = df_sensors[df_sensors['sensor_in_id'].
            isin(df_sum['sensor_id'].tolist())]['sensor_out_id'].tolist()

        # Write processed values to database
        df_sum.to_sql(name='meas', con=engine, if_exists='append', index=False)
    else:
        nebula_client.warning('Daily sum: no data!')


def daily_cum_sum(df_sensors):
    query = 'SELECT DATE(timestamp) as timestamp, sensors.id as sensor_id, meas.value FROM meas ' \
            'LEFT JOIN sensors ON meas.sensor_id = sensors.id WHERE sensors.id IN (%s) ' \
            'AND DATE(timestamp) = DATE(DATE_SUB(NOW(), INTERVAL 1 DAY))' %\
            ", ".join(map(str, df_sensors['sensor_in_id']))
    df = pd.read_sql_query(query, con=engine)
    if not df.empty:
        nebula_client.info('Daily cumulative sum: %d values to process' % len(df.index))

        # Compute daily sum
        df_sum = df.groupby(['timestamp', 'sensor_id'], as_index=False).agg(np.ptp)
        df_sum['sensor_id'] = df_sensors[df_sensors['sensor_in_id'].
            isin(df_sum['sensor_id'].tolist())]['sensor_out_id'].tolist()
        print(df_sum)
        # Write processed values to database
        df_sum.to_sql(name='meas', con=engine, if_exists='append', index=False)
    else:
        nebula_client.warning('Daily cumulative sum: no data!')


def weekly_sum(df_sensors):
    if calendar.day_name[datetime.today().weekday()] == 'Monday':
        query = 'SELECT WEEK(timestamp) as timestamp, sensors.id as sensor_id, meas.value FROM meas ' \
                'LEFT JOIN sensors ON meas.sensor_id = sensors.id WHERE sensors.id IN (%s) ' \
                'AND DATE(timestamp) > DATE(DATE_SUB(NOW(), INTERVAL 7 DAY))' %\
                ", ".join(map(str, df_sensors['sensor_in_id']))
        df = pd.read_sql_query(query, con=engine)
        if not df.empty:
            nebula_client.info('Weekly sum: %d values to process' % len(df.index))

            # Compute daily sum
            df_sum = df.groupby(['timestamp', 'sensor_id'], as_index=False).sum()
            df_sum['sensor_id'] = df_sensors['sensor_out_id']
            df_sum['timestamp'] = (datetime.now()+relativedelta(days=-7)).strftime("%Y-%m-%d")

            print(df_sum)

            # Write processed values to database
            df_sum.to_sql(name='meas', con=engine, if_exists='append', index=False)
        else:
            nebula_client.warning('Weekly sum: no data!')


def monthly_sum(df_sensors):
    if datetime.today().day == 1:
        query = 'SELECT MONTH(timestamp) as timestamp, sensors.id as sensor_id, meas.value FROM meas ' \
                'LEFT JOIN sensors ON meas.sensor_id = sensors.id WHERE sensors.id IN (%s) ' \
                'AND MONTH(timestamp) = MONTH(DATE_SUB(NOW(), INTERVAL 1 MONTH))' %\
                ", ".join(map(str, df_sensors['sensor_in_id']))
        df = pd.read_sql_query(query, con=engine)
        if not df.empty:
            nebula_client.info('Monthly sum: %d values to process' % len(df.index))

            # Compute daily sum
            df_sum = df.groupby(['timestamp', 'sensor_id'], as_index=False).sum()
            df_sum['sensor_id'] = df_sensors['sensor_out_id']
            df_sum['timestamp'] = (datetime.now() + relativedelta(months=-1)).strftime("%Y-%m-%d")

            # Write processed values to database
            df_sum.to_sql(name='meas', con=engine, if_exists='append', index=False)
        else:
            nebula_client.warning('Monthly sum: no data!')


def yearly_sum(df_sensors):
    if datetime.today().day == 1 and calendar.month_name[datetime.today().month] == 'January':
        query = 'SELECT YEAR(timestamp) as timestamp, sensors.id as sensor_id, meas.value FROM meas ' \
                'LEFT JOIN sensors ON meas.sensor_id = sensors.id WHERE sensors.id IN (%s) ' \
                'AND YEAR(timestamp) = YEAR(DATE_SUB(NOW(), INTERVAL 1 YEAR))' %\
                ", ".join(map(str, df_sensors['sensor_in_id']))
        df = pd.read_sql_query(query, con=engine)
        if not df.empty:
            nebula_client.info('Yearly sum: %d values to process' % len(df.index))

            # Compute daily sum
            df_sum = df.groupby(['timestamp', 'sensor_id'], as_index=False).sum()
            df_sum['sensor_id'] = df_sensors['sensor_out_id']
            df_sum['timestamp'] = (datetime.now() + relativedelta(years=-1)).strftime("%Y-%m-%d")

            # Write processed values to database
            df_sum.to_sql(name='meas', con=engine, if_exists='append', index=False)
        else:
            nebula_client.warning('Yearly sum: no data!')


algorithm_map = {
    'daily_cum_sum': daily_cum_sum,
    'daily_sum': daily_sum,
    'weekly_sum': weekly_sum,
    'monthly_sum': monthly_sum,
    'yearly_sum': yearly_sum
}

# Load configuration YAML
path = os.path.dirname(os.path.realpath(__file__))
fp = open(path + '/config.yaml', 'r')
cfg = yaml.load(fp)

# Set up Nebula API client
nebula_client = nebula.Client(**cfg['nebula'])

if __name__ == "__main__":
    # Connect to MySQL server
    engine = create_engine(url.URL(**cfg['mysql']))
    conn = engine.connect()

    # Get list of algorithms
    query = 'SELECT * FROM algorithms'
    df = pd.read_sql_query(query, con=engine, index_col='id')

    for id, row in df.iterrows():
        query = 'SELECT sensor_in_id, sensor_out_id FROM algorithms_sensors WHERE algorithm_id = %s' % id
        df = pd.read_sql_query(query, con=engine)
        algorithm_map[row['name']](df)
