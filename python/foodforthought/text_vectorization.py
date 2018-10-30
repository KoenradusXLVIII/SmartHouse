import csv
import random
import skipthoughts

# Load training data
f = open('train.csv', encoding="utf8")
train_rows = [row for row in csv.reader(f)][1:]  # discard the first row
random.shuffle(train_rows)
tweets_train = [row[0] for row in train_rows]
classes_train = [row[1] for row in train_rows]

# Load testing data
f = open('test.csv', encoding="utf8")
test_rows = [row for row in csv.reader(f)][1:]  # discard the first row
tweets_test = [row[0] for row in test_rows]
classes_test = [row[1] for row in test_rows]

class SkipThoughtsVectorizer(object):
    def __init__(self, **kwargs):
        self.model = skipthoughts.load_model()
        self.encoder = skipthoughts.Encoder(self.model)

    def fit_transform(self, raw_documents, y):
        return self.encoder.encode(raw_documents, verbose=False)

    def fit(self, raw_documents, y=None):
        self.fit_transform(raw_documents, y)
        return self

    def transform(self, raw_documents, copy=True):
        return self.fit_transform(raw_documents, None)