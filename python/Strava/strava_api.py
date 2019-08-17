# Global imports
from stravalib.client import Client
import pandas as pd
import os

# Snippet to get new code
# url = client.authorization_url(client_id=dfAPI['client_id'], redirect_uri='http://127.0.0.1:5000/authorization')
# print(url)

def strava_data(fp):
    # Configuration
    cols = ['id', 'name', 'type', 'start_date_local', 'average_heartrate', 'distance', 'average_speed',
            'elapsed_time']

    # Initialise object and get access token
    dfAPI = pd.read_csv('api.key')
    client = Client()
    access_token = client.exchange_code_for_token(client_id=dfAPI['client_id'], client_secret=dfAPI['client_secret'],
                                                  code=dfAPI['code'])
    print('Access token: %s' % access_token['access_token'])

    if os.path.isfile(fp):
        # Read local database
        df = pd.read_csv(fp, index_col='id')
        df = df.sort_values(by=['id'], ascending=False)
        last_id = int(df.head(1).index[0])
        last_start_date = str(df['start_date_local'].head(1).values[0])
        print('Local database has %d entries' % len(df.index))
    else:
        # Prepare empty DataFrame
        df = pd.DataFrame(columns=cols)
        df.set_index('id', drop=True, inplace=True)
        last_id = 0
        last_start_date = None

    # Check to see if new data is uploaded to Strava
    print('Accessing API to check for new acitivties')
    last_upload = client.get_activities(limit=1)
    last_upload = last_upload.next()
    if int(last_upload.id) != last_id:
        # One or more new activities have been upload
        # Download actitives in batches fof 10 until we
        # reach the last uploaded activity already in the DB
        print('New uploads detected; downloading...')
        new_uploads = 0
        activities = client.get_activities(after=last_start_date)
        data = []
        for activity in activities:
            if int(activity.id) != last_id:
                new_uploads += 1
                my_dict = activity.to_dict()
                data.append([activity.id] + [my_dict.get(x) for x in cols[1:]])
            else:
                # All new activities processed
                break

        # Store new uploads to temporary DataFrame
        print('%d actitivies downloaded and added to database' % new_uploads)
        df_new = pd.DataFrame(data, columns=cols)
        df_new['average_speed'] *= 3.6
        df_new['distance'] /= 1000
        df_new.set_index('id', drop=True, inplace=True)
        df = pd.concat([df, df_new])
        df.sort_values(by=['id'], ascending=False, inplace=True)
        print('Local database now has %d entries' % len(df.index))
    else:
        print('Database up to date, no new activities uploaded')

    df.to_csv(fp)
    return df
