"""
Model tuning.

Input:
    Raw data

Output:
    Printed diagnostics
    Pickled model
"""

import os
import sys
import time
import numpy as np
import datetime as dt
from dataload import dataload
from xgboost import XGBRegressor
from sklearn.model_selection import KFold, \
    GridSearchCV, cross_val_score
from sklearn.metrics import r2_score
from sklearn.metrics import mean_squared_error as mse
from sklearn.ensemble import RandomForestRegressor, AdaBoostRegressor
from sklearn.externals import joblib

def main():
    print('Running', sys.argv[0], sys.argv[1])
    start_time = time.perf_counter()
    today = dt.datetime.today().strftime('%Y%m%d_%H%M%S')
    algo = str(sys.argv[1])
    random_state = np.random.randint(1000000)

    path = 'output/'

    try:
        os.mkdir(path)
    except OSError:
        print(f'Creation of {path} failed')
    else:
        print(f'Successfully created the directory {path}')

    # Load data
    Xtrain, Xtest, ytrain, ytest = dataload()

    # Check pairwise correlation
    def corrprint(df, threshold=0.7):
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
            'n_estimators': [50, 100, 150, 200],
            'max_depth': [50, 100, 250, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 3, 4],
            'bootstrap': [True, False],
            'max_features': ['auto', 0.33],
            }

    xg_params = {
            'eta': [0, 0.01, 0.05, 0.1, 0.15, 0.2],
            'gamma': np.arange(0, 55, 5),
            'max_depth': np.arange(0, 24, 3),
            }

    ada_params = {
            'n_estimators': np.arange(50, 500, 10),
            'loss': ['linear', 'square', 'exponential']
            }

    params = {
            'rf': rf_params,
            'xg': xg_params,
            'ada': ada_params,
            }

    regs = {
            'rf': RandomForestRegressor(max_depth=None),
            'xg': XGBRegressor(booster='gbtree'),
            'ada': AdaBoostRegressor(random_state=random_state)
            }

    print('\nRandom_state for KFold: ', random_state)
    cv = KFold(n_splits=12, shuffle=True, random_state=random_state)

    search = GridSearchCV(
            estimator=regs[algo],
            param_grid=params[algo],
            scoring='r2',
            cv=cv,
            verbose=1,
            n_jobs=-1
            )

    ''' Model Fitting, Pickling '''

    search.fit(Xtrain, ytrain)
    model = search.best_estimator_
    print(model)
    joblib.dump(model, path + f'{algo}_{today}.pkl')

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

    end_time = (time.perf_counter() - start_time)/60
    print(f'Runtime: {round(end_time, 2)} minutes')

if __name__ == '__main__':
    main()
