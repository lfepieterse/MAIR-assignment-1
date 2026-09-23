import argparse
import os
import sys

# Import the functions from other modules
from data_loader import load_data
from models import train_tfidf_vectorizer, train_logistic_regression
from evaluate import evaluate_held_out

TRAIN_DATA_PATH = "./data/dialog_acts.dat"
TEST_DATA_PATH = None #replace this

def interactive():
    {}#to do in 1b
    

def main(train_path, test_path):
    
    df_train = load_data(train_path)
    X_train_features, vectorizer = train_tfidf_vectorizer(df_train['utterance'])
    y_train = df_train['label']
    
    
    model = train_logistic_regression(X_train_features, y_train)
    #model = train_SVM(X_train_features, y_train)

    if test_path:
        df_test = load_data(test_path)
        
        # Transform the test utterances using the fitted vectorizer
        X_test_features = vectorizer.transform(df_test['utterance'])
        predictions = model.predict(X_test_features)
        evaluate_held_out(df_test['label'], predictions, "Logistic Regression")
 

if __name__ == "__main__":
    