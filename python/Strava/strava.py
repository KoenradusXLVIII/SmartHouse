from stravalib.client import Client
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Global configuration
pd.set_option('display.max_columns', None)

# API settings
client_id = '32388'
client_secret = 'c77572ad9ca4ebce7753b4bb51cf75ee6d0094e2'
code = 'dd495140777ede94bed8b98d7debe151bacd4ca6'


def download(fp):
    # Snippet to get new code
    #url = client.authorization_url(client_id=client_id, redirect_uri='http://127.0.0.1:5000/authorization')

    # Initialise object and get access token
    client = Client()
    access_token = client.exchange_code_for_token(client_id=client_id, client_secret=client_secret, code=code)
    print('Access token: %s' % access_token['access_token'])

    limit = 10
    print('Accessing API to retrieve the latest %d activities' % limit)
    activities = client.get_activities(limit=limit)


    # Convert data to Pandas dataframe
    cols =['name', 'start_date_local', 'average_heartrate', 'distance', 'average_speed', 'elapsed_time']
    data = []
    for activity in activities:
        my_dict = activity.to_dict()
        data.append([my_dict.get(x) for x in cols])
    df = pd.DataFrame(data, columns=cols)
    df.to_csv(fp)

    return df


def main():
    strava_fp = 'strava_data.csv'

    # Get data
    if os.path.exists(strava_fp):
        print('Reading from \'%s\'' % strava_fp)
        df = pd.read_csv(strava_fp)
    else:
        df = download(strava_fp)

    # Filtering
    df_selected = df[df['name'].str.contains('Maffetone')]
    df_selected = df_selected.sort_values('start_date_local')
    print(df_selected)

    # Plotting
    fig, ax1 = plt.subplots()
    x = df_selected['start_date_local']

    # Left axis
    y = df_selected['average_heartrate']
    ax1.scatter(x, y, color='b')
    z = np.polyfit(range(len(y)), y, 1)
    p = np.poly1d(z)
    ax1.plot(x, p(range(len(y))), "b--")
    ax1.set_ylabel('Heartrate [BPM]')

    # Right axis
    ax2 = ax1.twinx()
    y = df_selected['average_speed']*3.6
    ax2.scatter(x, y, color='r')
    z = np.polyfit(range(len(y)), y, 1)
    p = np.poly1d(z)
    ax2.plot(x, p(range(len(y))), "r--")
    ax2.set_ylabel('Speed [km/h]')

    # General plot styling
    fig.tight_layout()
    plt.title('Maffetone progress')
    ax1.set_xlabel('Date')
    plt.show()

if __name__ == '__main__':
   main()