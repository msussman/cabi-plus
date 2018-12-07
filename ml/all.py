"""
Super long/messy script from data generation to model tuning.

Input:
    Raw data

Output:
    Pickled model (rf or xgboost), feature importances csv
"""

import sys
import sqlite3
import time
import pandas as pd
import numpy as np
import datetime as dt
from xgboost import XGBRegressor
from sklearn.model_selection import KFold, \
    GridSearchCV, cross_val_score
from sklearn.metrics import r2_score
from sklearn.metrics import mean_squared_error as mse
from sklearn.ensemble import RandomForestRegressor
from sklearn.externals import joblib

def everything():
    print('Running ', sys.argv[0], sys.argv[1])
    start_time = time.perf_counter()
    today = dt.datetime.today().strftime('%Y%m%d_%H%M%S')
    algo = str(sys.argv[1])

    ''' Data Preparation '''

    # Establish Connection
    con = sqlite3.connect(r'data/for_ml.db')
    cur = con.cursor()

    df = pd.read_sql("""SELECT
                        *
                        FROM final_db;
                        """, con=con)

    # Putting date in index
    df.set_index('date', inplace=True)
    df.index = pd.to_datetime(df.index)

    # Train-test split
    train = df.loc[:'2018-09-04']
    test = df.loc['2018-09-05':]

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
            'sunrisetime', 'sunsettime'
            ]

    drop_cols = target_cols + cabi_cols + other_cols
    feature_cols = [c for c in df.columns if c not in drop_cols]

    Xtrain = train[feature_cols]
    ytrain = train[target_cols[0]]
    Xtest = test[feature_cols]
    ytest = test[target_cols[0]]

    print('\n{} features: '.format(len(feature_cols)), feature_cols)
    print('\nTarget: ', target_cols[0])

    # Check pairwise correlation
    def corrprint(df, threshold=0.65):
        corr_df = df.corr()
        corred = np.where(np.abs(corr_df) > threshold)
        corred = [(corr_df.iloc[x,y], x, y) for x, y in zip(*corred) if x != y and x < y]
        s_corr_list = sorted(corred, key=lambda x: -abs(x[0]))
        print("\nThere are {} feature pairs with pairwise correlation above {}".format(len(s_corr_list), threshold))
        for v, i, j in s_corr_list:
            print("{} and {} = {:0.3f}".format(corr_df.index[i], corr_df.columns[j], v))

    corrprint(Xtrain)

    ''' Hyperparameter Tuning '''

    rf_params = {
            'n_estimators': [50, 100, 150, 200, 250],
            'max_depth': [50, 100, 250, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 3, 4],
            'bootstrap': [True, False],
            'max_features': ['auto', 'sqrt'],
            }

    xg_params = {
            'eta': np.arange(0, 1.1, .1),
            'gamma': np.arange(0, 55, 5),
            'max_depth': np.arange(0, 24, 3),
            }

    params = {
            'rf': rf_params,
            'xg': xg_params
            }

    regs = {
            'rf': RandomForestRegressor(max_depth=None),
            'xg': XGBRegressor(booster='gbtree')
            }

    reg = regs[algo]
    random_state = np.random.randint(1000000)
    print('\nRandom_state for KFold: ', random_state)
    cv = KFold(n_splits=12, shuffle=True, random_state=random_state)

    search = GridSearchCV(
            estimator=reg,
            param_grid=params[algo],
            scoring='r2',
            cv=cv,
            verbose=1,
            n_jobs=-1
            )

    ''' Model Fitting, Pickling '''

    search.fit(Xtrain, ytrain)
    model = search.best_estimator_
    print('\n', model)
    joblib.dump(model, f'output/{algo}_{today}.pkl')

    ''' Diagnostics and Output '''

    def cv_score(model, n_splits=12):
        """
        Evaluates a model by 12-fold cross-validation and
        prints mean and 2*stdev of scores.
        """
        kf = KFold(n_splits=n_splits, shuffle=True)
        scores = cross_val_score(model, Xtrain, ytrain, cv=kf,
                                 scoring=None,
                                 n_jobs=-1, verbose=3)
        print(scores)
        print("R^2: {:0.3f} (+/- {:0.3f})".format(scores.mean(), scores.std() * 2))

    def score_model(model):
        """
        Fits a model using the training set, predicts using the test set, and then calculates
        and reports goodness of fit metrics.
        """
        model.fit(Xtrain, ytrain)
        yhat = model.predict(Xtest)
        r2 = r2_score(ytest, yhat)
        me = mse(ytest, yhat)
        print("Results from {}: \nr2={:0.3f} \nMSE={:0.3f}".format(model, r2, me))

    print(f'12-fold CV score for {algo}: \n')
    cv_score(model)
    print(f'Train-test-split score for {algo}: \n')
    score_model(model)

    feature_importances = pd.DataFrame(model.feature_importances_,
                                       index=Xtrain.columns,
                                       columns=['importance']).sort_values('importance', ascending=False)

    feature_importances.to_csv(f'output/{algo}_feature_importances_{today}.csv')

    end_time = (time.perf_counter() - start_time)/60
    print(f'Runtime: {round(end_time, 2)} minutes')

if __name__ == '__main__':
    everything()
