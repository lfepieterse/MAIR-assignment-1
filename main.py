import argparse
import os
import sys

# Import the functions from other modules
from data_loader import load_data, create_original_split, create_grouped_split
from models import (
    rule_based_classifying,
    train_tfidf_vectorizer, 
    train_logistic_regression, 
    train_SVM, 
    get_embeddings
)
from evaluate import evaluate_test

TRAIN_DATA_PATH = "./data/dailog_acts.dat"
TEST_DATA_PATH = None #replace this

def interactive(model, feature_extractor, model_type):
    print("\n Dialog system")
    print("To stop, type 'quit'.")
    
    while True:
        user_input = input("You: ")
        
        if user_input.strip().lower() == 'quit':
            print("Quitting")
            break
            
        input_lowered = user_input.lower()
        
        if model_type == 'tfidf':
            features = feature_extractor.transform([input_lowered])
        else:
            features = get_embeddings([input_lowered], batch_size=1)
            
        prediction = model.predict(features)[0]
        print(f"Predicted of dialog act: [{prediction}]\n")
    

def main(train_path, test_path, model_type):
    print("choose the classifier you would like to run:")
    print("A = SVM")
    print("B = Logistic Regression")
    choice = input("Type A,  or B:").strip().upper()
    
    if choice == "A":
        classifier = "SVM"
    if choice == "B":
        classifier = "Logistic Regression"
    
    df = load_data(train_path)
    
    runs = [] 
    
    if test_path:
        df_test = load_data(test_path)
        runs.append(("held out test set", df, df_test))
    else: #if not tested by grader, using development set, so split data
        print("creating original and grouped splits")
        df_train_original, df_test_original = create_original_split(df)
        df_train_grouped, df_test_grouped = create_grouped_split(df)
        runs.append(("original split (85/15)", df_train_original, df_test_original))
        runs.append(("grouped split", df_train_grouped, df_test_grouped))
       
    #evaluating rule-based baseline
    print("Evaluating the rule-based baseline")
    for split_name, _, split_test in runs:
        baseline_predictions = split_test['utterance'].apply(rule_based_classifying)
        evaluate_test(split_test['label'], baseline_predictions, f"Rule-Based Baseline ({split_name})")
    
    print(f"\n training and evaluating {model_type.upper()} with {classifier}")
    
    active_model = None
    active_extractor = None

    for split_name, split_train, split_test in runs:
        print(f"\busy with {split_name}...")
        if model_type == 'tfidf':
            X_train_features, active_extractor = train_tfidf_vectorizer(split_train['utterance'])
            X_test_features = active_extractor.transform(split_test['utterance'])
        elif model_type == 'distilbert':
            X_train_features = get_embeddings(split_train['utterance'].tolist(), batch_size=32)
            X_test_features = get_embeddings(split_test['utterance'].tolist(), batch_size=32)
            active_extractor = None
            
        y_train = split_train['label'] 
      
        if classifier == "SVM":
            active_model = train_SVM(X_train_features, y_train)
        if classifier == "Logistic Regression":
            active_model = train_logistic_regression(X_train_features, y_train)

        predictions = active_model.predict(X_test_features)
        evaluation = f"{model_type.upper()} + {classifier} ({split_name})"
        evaluate_test(split_test['label'], predictions, evaluation)
        
    if not test_path:
        interactive(active_model, active_extractor, model_type)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline classifier of the dialog act")
    
    parser.add_argument(
        "--train_data", 
        type=str, 
        default="./data/dailog_acts.dat",
        help="Path to training dataset."
    )
    
    parser.add_argument(
        "--test_data", 
        type=str, 
        default=None,
        help="FOR GRADING: Path to test dataset."
    )
    
    parser.add_argument(
        "--model_type", 
        type=str, 
        choices=['tfidf', 'distilbert'],
        default='tfidf',
        help="Choose feature extraction method: 'tfidf' or 'distilbert'."
    )
    
    args = parser.parse_args()
    main(args.train_data, args.test_data, args.model_type)