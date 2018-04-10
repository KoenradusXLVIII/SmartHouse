import pandas as pd
import glob, os

# Concatenate files
df = pd.concat(map(pd.read_csv, glob.glob(os.path.join('', 'data/PVOutput-P-20-*.csv'))))
df.to_csv('data/PVOutput-P-20.csv')