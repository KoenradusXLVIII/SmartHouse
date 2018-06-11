import json
import requests
import yaml
import os

# Load configuration YAML
path = os.path.dirname(os.path.realpath(__file__))
cfg = yaml.load(open(path + '/config.yaml', 'r'))

def main():
    country_list = read_redlist('country/list')
    print(country_list)

def read_redlist(function):
    r = requests.get(cfg['redlist']['baseurl'] + function + '?token=' + cfg['redlist']['token'])
    return r.text

if __name__ == "__main__":
    main()
