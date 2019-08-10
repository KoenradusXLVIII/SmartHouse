from stravalib.client import Client
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import time

# Global configuration
pd.set_option('display.max_columns', None)
pd.set_option('expand_frame_repr', False)


def download(fp):
    dfAPI = pd.read_csv('api.key')

    # Snippet to get new code
    #url = client.authorization_url(client_id=dfAPI['client_id'], redirect_uri='http://127.0.0.1:5000/authorization')
    #print(url)

    # Initialise object and get access token
    client = Client()
    access_token = client.exchange_code_for_token(client_id=dfAPI['client_id'], client_secret=dfAPI['client_secret'],
                                                  code=dfAPI['code'])
    print('Access token: %s' % access_token['access_token'])

    limit = 1000
    print('Accessing API to retrieve the latest %d activities' % limit)
    activities = client.get_activities(limit=limit)


    # Convert data to Pandas dataframe
    cols =['name', 'type', 'start_date_local', 'average_heartrate', 'distance', 'average_speed', 'elapsed_time']
    data = []
    for activity in activities:
        my_dict = activity.to_dict()
        data.append([my_dict.get(x) for x in cols])
    df = pd.DataFrame(data, columns=cols)
    df['average_speed'] *= 3.6
    df['distance'] /= 1000
    df.to_csv(fp)

    return df


def main():
    strava_fp = 'strava_data.csv'

    # Get data
    force_download = True
    local_copy_outdated = True
    if os.path.exists(strava_fp):
        creation_time = os.path.getmtime(strava_fp)
        if ((time.time() - creation_time) < (24 * 3600)) and not force_download:
            # File is less then a day old, let's not download the data again
            local_copy_outdated = False
            print('Reading from \'%s\'' % strava_fp)
            df = pd.read_csv(strava_fp)

    if local_copy_outdated:
        print('Downloading data from Strava website')
        df = download(strava_fp)

    # Filtering
    df_selected = df[df['type'] == 'Run']
    df_selected = df_selected[df_selected['name'].str.contains('Maffetone')]
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
    y = df_selected['average_speed']
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