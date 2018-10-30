import pandas as pd
import glob, os

# Concatenate files
df = pd.concat(map(pd.read_csv, glob.glob(os.path.join('', 'data/PVOutput-P-20-*.csv'))))
df['POWER_OUT'] = (df['ENERGY_OUT'].shift(-1) - df['ENERGY_OUT']).shift(1)
df['POWER_IN'] = (df['ENERGY_IN'].shift(-1) - df['ENERGY_IN']).shift(1)
df.to_csv('data/PVOutput-P-20.csv')