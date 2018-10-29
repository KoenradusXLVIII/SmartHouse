import json
import requests
import yaml
import os
from pprint import pprint
from time import sleep

# Load configuration YAML
path = os.path.dirname(os.path.realpath(__file__))
cfg = yaml.load(open(path + '/config.yaml', 'r'))


def main():
    mammals = read_redlist(cfg['redlist']['mammel_url'])
    total_mammels = len(mammals['result']);
    cnt = 0
    for animal in mammals['result']:
        cnt += 1
        try:
            with open(cfg['redlist']['mammel_file']) as fp:
                data = json.load(fp)
        except:
            data = []

        in_database = False
        for item in data:
            if str(animal['taxonid']) == item['name']:
                print('[{}/{}] Skipping data write for id: {}'.format(cnt, total_mammels, item['name']))
                in_database = True
                break

        if not in_database:
            # Read animal details
            mammal_details = read_redlist('{}{}'.format('species/history/id/', animal['taxonid']))
            print('[{}/{}] Writing data to file for id: {}'.format(cnt, total_mammels, mammal_details['name']))

            # Append to local database
            data.append(mammal_details)
            with open(cfg['redlist']['mammel_file'], 'w') as fp:
                json.dump(data, fp)

            # Do not overload API
            sleep(10)


def read_redlist(function):
    for retry in range(5):
        try:
            r = requests.get(cfg['redlist']['baseurl'] + function + '?token=' + cfg['redlist']['token'])
            if (r.status_code == 200):  # Valid response received
                return json.loads(r.text)
            else:
                print('Invalid response. Status code: {}. Iteration {}.'.format(r.status_code, retry))
        except:
            print('No response.')


if __name__ == "__main__":
    main()
