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
from dataload import dataload
from sklearn.externals import joblib
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import r2_score
from sklearn.metrics import mean_squared_error as mse

start_time = time.perf_counter()

def main():
    print('Printing from ', sys.argv[0], sys.argv[1])
    algo = sys.argv[1]

    # Load data
    Xtrain, Xtest, ytrain, ytest = dataload()

    # Load model
    model = joblib.load(glob.glob('output/*{}*.pkl'.format(algo))[0])

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