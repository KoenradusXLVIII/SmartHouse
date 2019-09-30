"""Strava module"""
# Global imports
import os
import pandas as pd
from stravalib.client import Client
from collections import namedtuple

# Snippet to get new code
# url = client.authorization_url(client_id=dfAPI['client_id'],
#                                redirect_uri='http://127.0.0.1:5000/authorization')
# print(url)

# CH2.33: Named tuples
Functions = namedtuple('Functions', 'name scope')

class Strava:
    """Class to interact with Strava API"""
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=invalid-name

    # CH1.5: Global variables in a class
    # CH1.5: Easy way to create a list
    cols = 'id name type start_date_local average_heartrate' \
           ' distance average_speed elapsed_time'.split()
    funcs = []

    def __init__(self, api_file, local_db_fp, verbose=False, update=True):
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
        self._verbose = verbose

        # Handle exceptions in requesting the access token
        if not self._access_token:
            raise ConnectionError('Client did not receive a valid access token')

        # Verify if local database exists
        if os.path.isfile(self._local_db_fp):
            # Read from file and sort by id
            if self._verbose:
                print('Reading local database from: %s' % self._local_db_fp)
            self._db = pd.read_csv(self._local_db_fp, index_col='id')
            self._db.sort_values(by=['id'], inplace=True)
        else:
            # Create new DataFrame
            self._db = pd.DataFrame(columns=self.cols)
            self._db.set_index('id', drop=True, inplace=True)

        if self._verbose:
            print('Local database contains %d entries' % len(self))

        if update:
            # Verify if local database up to date
            if not self._local_db_in_sync():
                if self._verbose:
                    print('Local database not in sync, downloading...')
                self._update_local_db()
                self._save_local_db()
                if self._verbose:
                    print('Local database now contains %d entries' % len(self))
            else:
                if self._verbose:
                    print('Local database in sync')

    def __repr__(self):
        return 'Strava(%d)' % len(self)

    def __len__(self):
        # CH1.5: Custom special method
        return len(self._db.index)

    def __getitem__(self, row):
        # CH1.5: Custom special method
        return self._db.iloc[[row]]

    def __call__(self):
        # CH5.152: Custom __call__ method
        self.update()
        if self._verbose:
            print('Update completed')

    def decorator_factory(scope):
        # CH 7.194: Decorators
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                self.funcs.append(Functions(func.__name__, scope))
                return func(self, *args, **kwargs)
            return wrapper
        return decorator

    @decorator_factory('private')
    def _last_local_id(self):
        if self:
            last_local_id = self._db.iloc[[-1]].index.item()
        else:
            last_local_id = None
        return last_local_id

    @decorator_factory('private')
    def _local_db_in_sync(self):
        activity = self._client.get_activities(limit=1)
        activity = activity.next()
        self._last_remote_id = int(activity.id)
        return self._last_remote_id == self._last_local_id()

    @decorator_factory('private')
    def _update_local_db(self):
        last_start_date = None
        if self:
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

    @decorator_factory('private')
    def _save_local_db(self):
        self._db.to_csv(self._local_db_fp)

    @decorator_factory('public')
    def update(self, in_memory=False):
        """Update local database and store to disk if requested"""
        self._update_local_db()
        if not in_memory:
            self._save_local_db()

    @decorator_factory('public')
    def filter(self, activity_type='', name=''):
        """Filter database based on activity type and name"""
        df = self._db
        if activity_type:
            df = df[df['type'].str.contains(activity_type)]
        if name:
            df = df[df['name'].str.contains(name)]

        return df
