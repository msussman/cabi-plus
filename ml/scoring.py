"""
Script for scoring already-tuned models.

Input:
    Raw data
    Pickled model

Output:
    Printed diagnostics
    Fitted vs. actual .png + .csv
    Feature importances .csv
"""

import os
import glob
import time
import sys
import pandas as pd
import datetime as dt
from dataload import dataload
from sklearn.externals import joblib
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import r2_score, mean_squared_error, \
    mean_absolute_error, mean_squared_log_error
import matplotlib.pyplot as plt

start_time = time.perf_counter()

def main():
    print('Printing from', sys.argv[0], sys.argv[1])
    algo = sys.argv[1]
    today = dt.datetime.today().strftime('%Y%m%d_%H%M%S')

    # New directory for output
    path = f'output/{algo}_{today}/'

    try:
        os.mkdir(path)
    except OSError:
        print(f'Creation of {path} failed')
    else:
        print(f'Successfully created the directory {path}')

    # Load data
    Xtrain, Xtest, ytrain, ytest = dataload()

    # Load model - sort by descending for the most recent
    model_name = sorted(glob.glob(f'output/*{algo}*.pkl'), reverse=True)
    print('Model: ', model_name[0])
    model = joblib.load(model_name[0])
    model.fit(Xtrain, ytrain)

    def cv_score(model, n_splits=12):
        """
        Evaluates a model by 12-fold cross-validation and
        prints mean and 2*stdev of scores.
        """
        kf = KFold(n_splits=n_splits, shuffle=True, random_state=7)
        scores = cross_val_score(model, Xtrain, ytrain, cv=kf,
                                 scoring=None,
                                 n_jobs=-1, verbose=1)
        print(scores)
        print("R^2: {:0.3f} (+/- {:0.3f})".format(scores.mean(), 2*scores.std()))

    print(f'12-fold CV score for {algo}: \n')
    cv_score(model)

    yhat = model.predict(Xtest)

    r2 = round(r2_score(ytest, yhat), 3)
    mse = round(mean_squared_error(ytest, yhat), 2)
    mae = round(mean_absolute_error(ytest, yhat), 2)
    msle = round(mean_squared_log_error(ytest, yhat), 2)

    print('\nR^2: ', r2)
    print('MSE: ', mse)
    print('MAE: ', mae)

    data = pd.DataFrame({'t': ytest.index,
                         'ytest': ytest,
                         'yhat': yhat,
                         'error': ytest - yhat})

    mbe = round(data['error'].sum()/len(data), 2)
    print(f'Mean Bias Error for {algo}: {mbe}')
    print('Positive MBE signifies underprediction overall')

    plt.plot('t', 'ytest', data=data, color='blue', linewidth=1, label='actual')
    plt.plot('t', 'yhat', data=data, color='orange', marker='o', linestyle="None", label='predicted', alpha=0.5)
    plt.plot('t', 'error', data=data, color='gray')
    plt.suptitle(f'{algo} results over the DoBi period')
    plt.title(f'r2: {r2}, mse: {mse}, mae: {mae}, msle: {msle}, mbe: {mbe}')
    plt.legend()
    plt.savefig(path + f'{algo}_results_{today}.png')

    # Save data from plot
    data.to_csv(path + f'{algo}_predicted_{today}.csv', index=False)

    # Save feature importances
    feature_importances = pd.DataFrame(
            model.feature_importances_,
            index=Xtrain.columns,
            columns=['importance']).sort_values('importance', ascending=False)

    feature_importances.to_csv(path + f'{algo}_features_{today}.csv')

    end_time = time.perf_counter() - start_time
    print(f'Runtime: {round(end_time, 2)} seconds')

if __name__ == '__main__':
    main()
