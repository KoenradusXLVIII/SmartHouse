import twitter
import yaml
import os
import json
import time
import requests

# Load configuration YAML
path = os.path.dirname(os.path.realpath(__file__))
cfg = yaml.load(open(path + '/config.yaml', 'r'))

api = twitter.Api(consumer_key=cfg['twitter']['consumer key'],
                      consumer_secret=cfg['twitter']['consumer secret'],
                      access_token_key=cfg['twitter']['access token'],
                      access_token_secret=cfg['twitter']['access token secret'],
                      tweet_mode=cfg['twitter']['tweet mode'])

stock_ticker = '$TSLA'

query = api.GetSearch(stock_ticker,count=100,result_type='recent')
for r in query:
    try:
        with open(cfg['twitter']['tweet base']) as fp:
            data = json.load(fp)
    except:
        data = []


    in_database = False
    for item in data:
        if r.id == item[0]:
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

        # Append to local database
        print('Writing data to file for tweet id {} by {}'.format(r.id, r.user.screen_name))
        data.append([r.id, r.created_at_in_seconds, r.user.id, r.user.screen_name, r.full_text, stock_open])
        with open(cfg['twitter']['tweet base'], 'w') as fp:
            json.dump(data, fp)
