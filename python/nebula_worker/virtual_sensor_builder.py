# Public packages
import os
import yaml
from sqlalchemy import create_engine
from sqlalchemy.engine import url
import pandas as pd
import numpy as np

# Load configuration YAML
path = os.path.dirname(os.path.realpath(__file__))
fp = open(path + '/config.yaml', 'r')
cfg = yaml.load(fp)

# Connect to MySQL server
engine = create_engine(url.URL(**cfg['mysql']))
conn = engine.connect()

sensor_id = 3

query = 'SELECT * FROM sensors where id=%d' % sensor_id
df = pd.read_sql(query, con=engine)

query = 'INSERT INTO sensors (`name`, `quantity_id`, `node_id`) VALUES (\'%s Daily Maximum\', \'%s\', \'%s\')' % (df.name[0], df.quantity_id[0], df.node_id[0])
result = conn.execute(query)
print(query)
query = 'INSERT INTO sensors (`name`, `quantity_id`, `node_id`) VALUES (\'%s Weekly Maximum\', \'%s\', \'%s\')' % (df.name[0], df.quantity_id[0], df.node_id[0])
result = conn.execute(query)
print(query)
query = 'INSERT INTO sensors (`name`, `quantity_id`, `node_id`) VALUES (\'%s Monthly Maximum\', \'%s\', \'%s\')' % (df.name[0], df.quantity_id[0], df.node_id[0])
result = conn.execute(query)
print(query)
query = 'INSERT INTO sensors (`name`, `quantity_id`, `node_id`) VALUES (\'%s Yearly Maximum\', \'%s\', \'%s\')' % (df.name[0], df.quantity_id[0], df.node_id[0])
result = conn.execute(query)
print(query)

