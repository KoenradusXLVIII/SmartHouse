# Global imports
from stravalib.client import Client
import pandas as pd
import os

# Snippet to get new code
# url = client.authorization_url(client_id=dfAPI['client_id'], redirect_uri='http://127.0.0.1:5000/authorization')
# print(url)

class Strava:
    # CH1.5: Global variables in a class
    # CH1.5: Easy way to create a list
    cols = 'id name type start_date_local average_heartrate distance average_speed elapsed_time'.split()

    def __init__(self, api_file, local_db_fp, verbose=False):
        # Read API parameters from CSV file
        if os.path.isfile(api_file):
            api = pd.read_csv(api_file)
        else:
            raise FileNotFoundError('API key file not found')

        # Initialise local variables and objects
        self._client_id = api['client_id']
        self._client_secret = api['client_secret']
        self._code = api['code']
        self._local_db_fp = local_db_fp
        self._client = Client()
        self._access_token = self._client.exchange_code_for_token(client_id=self._client_id,
                                                                  client_secret=self._client_secret,
                                                                  code=self._code)
        self._last_remote_id = None

        # Handle exceptions in requesting the access token
        if not self._access_token:
            raise ConnectionError('Client did not receive a valid access token')

        # Verify if local database exists
        if os.path.isfile(self._local_db_fp):
            # Read from file and sort by id
            if verbose:
                print('Reading local database from: %s' % self._local_db_fp)
            self._db = pd.read_csv(self._local_db_fp, index_col='id')
            self._db.sort_values(by=['id'], inplace=True)
        else:
            # Create new DataFrame
            self._db = pd.DataFrame(columns=self.cols)
            self._db.set_index('id', drop=True, inplace=True)

        if verbose:
            print('Local database contains %d entries' % len(self))

        # Verify if local database up to date
        if not self._local_db_in_sync():
            if verbose:
                print('Local database not in sync, downloading...')
            self._update_local_db()
            self._save_local_db()
            if verbose:
                print('Local database now contains %d entries' % len(self))
        else:
            if verbose:
                print('Local database in sync')

    def __repr__(self):
        return 'Strava(%d)' % len(self)

    def __len__(self):
        # CH1.5: Custom special method
        return len(self._db.index)

    def __getitem__(self, row):
        # CH1.5: Custom special method
        return self._db.iloc[[row]]

    def _last_local_id(self):
        if len(self):
            return self._db.iloc[[-1]].index.item()
        else:
            None

    def _local_db_in_sync(self):
        activity = self._client.get_activities(limit=1)
        activity = activity.next()
        self._last_remote_id = int(activity.id)
        return self._last_remote_id == self._last_local_id()

    def _update_local_db(self):
        last_start_date = None
        if len(self):
            last_start_date = str(self._db['start_date_local'].tail(1).values[0])
        activities = self._client.get_activities(after=last_start_date)
        data = []
        for activity in activities:
            if int(activity.id) != self._last_local_id():
                my_dict = activity.to_dict()
                data.append([activity.id] + [my_dict.get(x) for x in self.cols[1:]])
            else:
                # All new activities processed
                break

        df = pd.DataFrame(data, columns=self.cols)
        df['average_speed'] *= 3.6
        df['distance'] /= 1000
        df.set_index('id', drop=True, inplace=True)
        self._db = pd.concat([self._db, df])
        self._db.sort_values(by=['id'], inplace=True)

    def _save_local_db(self):
        self._db.to_csv(self._local_db_fp)

    def update(self, in_memory=False):
        self._update_local_db()
        if not in_memory:
            self._save_local_db()

    def filter(self, type='', name=''):
        df = self._db
        if type:
            df = df[df['type'].str.contains(type)]
        if name:
            df = df[df['name'].str.contains(name)]

        return df
