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
from sklearn.metrics import r2_score
from sklearn.metrics import mean_squared_error as mse
from sklearn.metrics import mean_absolute_error as mae
import matplotlib.pyplot as plt

start_time = time.perf_counter()

def main():
    print('Printing from ', sys.argv[0], sys.argv[1])
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
    filename = sorted(glob.glob(f'output/*{algo}*.pkl'), reverse=True)
    model = joblib.load(filename[0])
    model.fit(Xtrain, ytrain)

    # Printing random state for reproducibility
    # For now just using random_state=7
    #random_state = np.random.randint()
    #print('Seed:', random_state)

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

    def score_model(model):
        """
        Fits a model using the training set, predicts using the test set, and then calculates
        and reports goodness of fit metrics.
        """
        model.fit(Xtrain, ytrain)
        yhat = model.predict(Xtest)
        r2 = round(r2_score(ytest, yhat), 3)
        msqe = round(mse(ytest, yhat), 2)
        mabe = round(mae(ytest, yhat), 2)
        print(f'Results from {model}: \nr2={r2} \nMSE={msqe} \nMAE={mabe}')

    print(f'12-fold CV score for {algo} (full test set): \n')
    cv_score(model)
    print(f'Train-test-split score for {algo} (full test set): \n')
    score_model(model)

    yhat = model.predict(Xtest)

    r2 = round(r2_score(ytest, yhat), 3)
    msqe = round(mse(ytest, yhat), 2)
    mabe = round(mae(ytest, yhat), 2)
    error = ytest - yhat

    data = pd.DataFrame({'t': ytest.index,
                         'ytest': ytest,
                         'yhat': yhat,
                         'error': error})

    # Save plot
    plt.plot('t', 'ytest', data=data, color='blue', linewidth=1, label='actual')
    plt.plot('t', 'yhat', data=data, color='orange', marker='o', linestyle="None", label='predicted', alpha=0.5)
    plt.plot('t', 'error', data=data, color='gray')
    plt.suptitle(f'{algo} results over the DoBi period')
    plt.title(f'r2: {r2}, mse: {msqe}, mae: {mabe}')
    plt.legend()
    plt.savefig(path + f'{algo}_results_{today}.png')
    #plt.show()

    neterror = data['error'].sum()
    print(f'Net error for {algo}: {neterror}')
    print('Positive net error signifies underprediction (overall)')

    # Save data from plot
    data.to_csv(path + f'{algo}_predicted_{today}.csv', index=False)

    # Save feature importances
    feature_importances = pd.DataFrame(
            model.feature_importances_,
            index=Xtrain.columns,
            columns=['importance']).sort_values('importance', ascending=False)

    feature_importances.to_csv(path + f'{algo}_features_{today}.csv')

    end_time = (time.perf_counter() - start_time)/60
    print(f'Runtime: {round(end_time, 2)} minutes')

if __name__ == '__main__':
    main()