"""
For holding the data load script
"""

import sqlite3
import pandas as pd

def dataload():
    """
    Connects to the sqlite db and performs a train-test and X-y split.
    """
    con = sqlite3.connect(r'data/for_ml.db')

    df = pd.read_sql("""SELECT
                        *
                        FROM final_db;
                        """, con=con)

    # Putting date in index
    df.set_index('date', inplace=True)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    df.insert(0, 'time', range(0, len(df)))

    # Train-test split
    train = df.loc[:'2017-12-31']
    test = df.loc['2018-01-01':]

    # Possible target variables
    target_cols = [
            'cabi_trips', 'cabi_trips_Casual',
            'cabi_trips_Member', 'cabi_trips_Unknown'
            ]

    # Leaving these out for now
    cabi_cols = [
            'cabi_bikes_avail', 'cabi_stations', 'cabi_docks', 'cabi_util_rate'
            ]

    # High correlation with some other variable, irrelevant, or all 0
    # Can be included and excluded if need be
    other_cols = [
            'apparenttemperaturelow', 'temperaturelow', 'temperaturehigh',
            'year', 'quarter', 'dewpoint', 'nats_attendance', 'sleet',
            'windbearing', 'moonphase', 'apparenttemperaturehightime',
            'apparenttemperaturelowtime', 'precipintensity',
            'sunrisetime', 'sunsettime', 'dc_pop',
            ]

    drop_cols = target_cols + cabi_cols + other_cols
    feature_cols = [c for c in df.columns if c not in drop_cols]

    Xtrain = train[feature_cols]
    print('Xtrain shape: ', Xtrain.shape)
    ytrain = train[target_cols[0]]
    print('ytrain shape: ', ytrain.shape)
    Xtest = test[feature_cols]
    print('Xtest shape: ', Xtest.shape)
    ytest = test[target_cols[0]]
    print('ytest shape: ', ytest.shape)

    print('\n{} features: '.format(len(feature_cols)), feature_cols)
    print('\nTarget: ', target_cols[0])
    return Xtrain, Xtest, ytrain, ytest