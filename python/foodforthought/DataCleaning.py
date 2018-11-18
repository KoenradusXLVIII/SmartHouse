import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import lxml
from pprint import pprint
from bs4 import BeautifulSoup
import re

from nltk.tokenize import WordPunctTokenizer
tok = WordPunctTokenizer()

pat_mention = r'@[A-Za-z0-9_]+' #Remove @mentions
pat_http = r'https?://[^ ]+' #Remove links
pat_www = r'www.[^ ]+'
pat_letters_only = r'[^a-zA-Z]' # Remove numbers
combined_pat = r'|'.join((pat_mention, pat_http, pat_www))

negations_dic = {"isn't":"is not", "aren't":"are not", "wasn't":"was not", "weren't":"were not",
                "haven't":"have not","hasn't":"has not","hadn't":"had not","won't":"will not",
                "wouldn't":"would not", "don't":"do not", "doesn't":"does not","didn't":"did not",
                "can't":"can not","couldn't":"could not","shouldn't":"should not","mightn't":"might not",
                "mustn't":"must not"}

neg_pat = re.compile(r'\b(' + '|'.join(negations_dic.keys()) + r')\b')

def tweet_cleaner(text):
    soup = BeautifulSoup(text, 'lxml')
    souped = soup.get_text()
    stripped = re.sub(combined_pat, '', souped)
    lower_case = stripped.lower()
    neg_handled = neg_pat.sub(lambda x: negations_dic[x.group()], lower_case)
    letters_only = re.sub(pat_letters_only, ' ', neg_handled)
    words = [x for x in tok.tokenize(letters_only) if len(x) > 1]
    return (" ".join(words)).strip()

def main():
    cols = ['sentiment', 'id', 'date', 'query_string', 'user', 'text']
    df = pd.read_csv("training.1600000.processed.noemoticon.csv", header=None, names=cols, encoding='ISO-8859–1')
    df['pre_clean_len'] = [len(t) for t in df.text]

    print('Cleaning and parsing the tweets...\n')
    clean_tweet_texts = []
    for i in range(0, len(df)):
        if ((i + 1) % 10000 == 0):
            print('Tweets %d of %d has been processed' % (i + 1, len(df)))
        clean_tweet_texts.append(tweet_cleaner(df['text'][i]))

    clean_df = pd.DataFrame(clean_tweet_texts,columns=['text'])
    clean_df['target'] = df.sentiment

    clean_df.to_csv('clean_tweet.csv', encoding='utf-8')

if __name__ == "__main__":
    main()