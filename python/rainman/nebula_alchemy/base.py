# Public packages
import os
import yaml
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import url

# Load configuration YAML
path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
fp = open(path + '/config.yaml', 'r')
cfg = yaml.load(fp)

# Set up database environment
engine = create_engine(url.URL(**cfg['mysql']))
Session = sessionmaker(bind=engine)
Base = declarative_base()


