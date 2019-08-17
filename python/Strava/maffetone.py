# Global imports
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Local imports
from strava_api import strava_data

# Global configuration
pd.set_option('display.max_columns', None)
pd.set_option('expand_frame_repr', False)


def main():
    strava_fp = 'strava_data.csv'

    # Get data
    df = strava_data(strava_fp)

    # Filtering
    df_selected = df[df['type'] == 'Run']
    df_selected = df_selected[df_selected['name'].str.contains('Maffetone')]
    df_selected = df_selected.sort_values('start_date_local')
    print(df_selected)

    # Plotting
    fig, ax1 = plt.subplots()
    x = df_selected['start_date_local']

    # Left axis
    y = df_selected['average_heartrate']
    ax1.scatter(x, y, color='b')
    z = np.polyfit(range(len(y)), y, 1)
    p = np.poly1d(z)
    ax1.plot(x, p(range(len(y))), "b--")
    ax1.set_ylabel('Heartrate [BPM]', color='b')
    ax1.tick_params(axis='y', labelcolor='b')

    # Right axis
    ax2 = ax1.twinx()
    y = df_selected['average_speed']
    ax2.scatter(x, y, color='r')
    z = np.polyfit(range(len(y)), y, 1)
    p = np.poly1d(z)
    ax2.plot(x, p(range(len(y))), "r--")
    ax2.set_ylabel('Speed [km/h]', color='r')
    ax2.tick_params(axis='y', labelcolor='r')

    # General plot styling
    fig.tight_layout()
    plt.title('Maffetone progress')
    ax1.set_xlabel('Date')
    plt.show()

if __name__ == '__main__':
   main()