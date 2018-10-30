import twitter
import yaml
import os
import csv
import json
import time
import requests
from monkeylearn import MonkeyLearn

# Load configuration YAML
path = os.path.dirname(os.path.realpath(__file__))
cfg = yaml.load(open(path + '/config.yaml', 'r'))

api = twitter.Api(consumer_key=cfg['twitter']['consumer key'],
                      consumer_secret=cfg['twitter']['consumer secret'],
                      access_token_key=cfg['twitter']['access token'],
                      access_token_secret=cfg['twitter']['access token secret'],
                      tweet_mode=cfg['twitter']['tweet mode'])

stock_ticker = '$TSLA'

query = api.GetSearch(stock_ticker,count=10,result_type='recent')
for r in query:
    data =[]
    with open(cfg['twitter']['tweet base'], encoding='utf-8') as fp:
        data = csv.reader(fp)

        in_database = False
        for row in data:
            if(len(row)): # Process non-empty rows
                if r.id == row[0]:
                    print('Skipping data write for id {} by {}'.format(r.id, r.user.screen_name))
                    in_database = True
                    break

        if not in_database:
            # Gather stock data
            tweet_date = time.strftime('%Y%m%d', time.localtime(r.created_at_in_seconds))
            req = json.loads(requests.get(cfg['IEX']['base url'] + stock_ticker[-1:].lower() + '/chart/date/'+ tweet_date).text)

            stock_open = -1
            if len(req):
                stock_open = req[0]['open']

            # Determine sentiment
            ml = MonkeyLearn('c7e51f5e307a9379cfd9e25bdec164e9beaf15ca')
            data = [r.full_text]
            model_id = 'cl_qkjxv9Ly'
            sentiment = ml.classifiers.classify(model_id, data)

            # Append to local database
            print('Writing data to file for tweet id {} by {}'.format(r.id, r.user.screen_name))
            with open(cfg['twitter']['tweet base'], 'a', encoding='utf-8') as fpa:
                fpa.write('{}, {}, {}, {}, \'{}\', {}, {}, {}\n'.format(r.id, r.created_at_in_seconds, r.user.id, r.user.screen_name, r.full_text.replace('\n',''), stock_open, sentiment.body[0]['classifications'][0]['tag_name'], sentiment.body[0]['classifications'][0]['confidence']))