"""
Script for scoring already-tuned models.

Input:
    Pickled model, raw data

Output:
    Diagnostics, scores
"""

import glob
import time
import sys
import pandas as pd
import numpy as np
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

    # Load data
    Xtrain, Xtest, ytrain, ytest = dataload()

    # Load model
    model = joblib.load(glob.glob('output/*{}*.pkl'.format(algo))[0])

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
        msqe = mse(ytest, yhat)
        mabe = mae(ytest, yhat)
        print("Results from {}: \nr2={:0.3f} \nMSE={:0.3f} \nMAE={:0.3f}".format(model, r2, msqe, mabe))

    print(f'12-fold CV score for {algo}: \n')
    cv_score(model)
    print(f'Train-test-split score for {algo}: \n')
    score_model(model)
    model.fit(Xtrain, ytrain)

    yhat = model.predict(Xtest)
    error = ytest - yhat

    data = pd.DataFrame({'t': ytest.index,
                         'ytest': ytest,
                         'yhat': yhat,
                         'error': error})

    plt.plot('t', 'ytest', data=data, color='blue', linewidth=1, label='actual')
    plt.plot('t', 'yhat', data=data, color='orange', marker='o', linestyle="None", label='predicted', alpha=0.5)
    plt.plot('t', 'error', data=data, color='gray')
    plt.legend()
    plt.show()
    plt.savefig(f'output/{algo}_results.png')

    neterror = data['error'].sum()
    print(f'On net, our errors are {neterror}')
    print('Positive net error signifies underprediction (on average)')

    end_time = (time.perf_counter() - start_time)/60
    print(f'Runtime: {round(end_time, 2)} minutes')

if __name__ == '__main__':
    main()