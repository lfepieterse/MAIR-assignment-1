import argparse
import os
import sys
import joblib

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
from dialogue_state import create_dialogue, END
from dialogue_manager import transition

from restaurant_repository import load_restaurants

TRAIN_DATA_PATH = "./data/dailog_acts.dat"
TEST_DATA_PATH = "./data/dialog_acts_test.dat" #for grader, check if the name is correct with the test data file!

#for 1a
def interactive(trained_models, feature_extractor, model_type):
    print("\n Dialog system")
    classifiers_active = " & ".join(trained_models.keys())
    print("To stop, type 'quit'.")
    
    while True:
        user_input = input("You: ")
        
        #If don't want to input an (other) utterance, type quit
        if user_input.strip().lower() == 'quit':
            print("Quitting")
            break
            
        input_lowered = user_input.lower() #process input
        
        if model_type == 'tfidf':
            features = feature_extractor.transform([input_lowered]) #vectorizer if tfidf
        else:
            features = get_embeddings([input_lowered], batch_size=1) #for distilbert need embeddings
        
        for classifier, model in trained_models.items():
            prediction = model.predict(features)[0]
            #make prediction for what dialog act the classifier would predict for utterance
            print(f"{classifier} dialog acts predicted: {prediction}") 
            
#for 1b
def interactive_dialogue(model, feature_extractor, model_type):
    dialogue = create_dialogue()
    
    #give user choice to see reasoning
    choice= input("Show reasoning explanations? Type yes or no:").strip().lower()
    while choice not in {"yes", "no"}:
        input("Type yes or no:").strip().lower()
    if choice == "yes":
        dialogue["show_reasoning"] = choice  #gets value True for "yes"
        
    dialogue["fallback_method"] = "levenshtein" #because semantic matching does not exist yet
    
    
    
    dialogue["restaurants"] = load_restaurants(
    "./data/restaurant_info_extended.csv"
)
    
    _, response = transition(dialogue, "hello")
    print(response)
    
    while dialogue["state"] != END:
        user_text = input("You: ").strip().lower()
        
        if user_text == "quit": break
        if not user_text: continue
        
        if model_type == "tfidf":
            features = feature_extractor.transform([user_text])
        else:
            features = get_embeddings(
                [user_text],
                batch_size=1
            )
        dialogue_act = model.predict(features)[0]
        
        _, response = transition(
            dialogue,
            dialogue_act,
            user_text
        )
       
        print(response)

def main(train_path, test_path, dialogue_only=False):

    #testing mode: load a saved model and start the dialogue
    if dialogue_only:
        print("Choose the saved feature extraction method:")
        print("A = TF-IDF")
        print("B = DistilBERT")
        feature_choice = input("Type A or B: ").strip().upper()

        model_type = "tfidf" if feature_choice == "A" else "distilbert"

        print("Choose the saved classifier:")
        print("A = SVM")
        print("B = Logistic Regression")
        classifier_choice = input("Type A or B: ").strip().upper()

        classifier_name = (
            "SVM" if classifier_choice == "A"
            else "Logistic Regression"
        )
        classifier_file = classifier_name.lower().replace(" ", "_")

        filename = f"original_{model_type}_{classifier_file}.joblib"
        artifact_path = os.path.join("saved_models", filename)

        if not os.path.exists(artifact_path):
            print("Saved model not found.")
            print("Run the full training pipeline first, with this model selected.")
            return

        saved = joblib.load(artifact_path)

        print("Loaded saved model. Starting dialogue...")
        interactive_dialogue(
            saved["model"],
            saved["extractor"],
            saved["model_type"],
        )
        return
    
    #Choose extraction method
    print("Choose feature extraction method:")
    print("  A = TF-IDF")
    print("  B = DistilBERT ")
    print("  C = Both ")
    choice1 = input("Type A, B, or C: ").strip().upper()
    
    if choice1 == "A":
        model_types_to_run = ["tfidf"]
    elif choice1 == "B":
        model_types_to_run = ["distilbert"]
    else:
        model_types_to_run = ["tfidf","distilbert"]
    
    #Here the user gets the question which classifier they want to use
    print("\nChoose the classifier you would like to run:")
    print("  A = SVM")
    print("  B = Logistic Regression")
    print("  C = Both")
    choice2 = input("Type A, B, or C: ").strip().upper()
    
    if choice2 == "A":
        classifiers_to_run = ["SVM"]
    elif choice2 == "B":
        classifiers_to_run = ["Logistic Regression"]
    else:
        classifiers_to_run = ["SVM", "Logistic Regression"]
    
    
    #choose if want to test with development or held-out test set
    print("\nChoose if you want to test on development or held-out test-set:")
    print("  A = train and evaluate on local validation (original & grouped splits + input utterance interactively)")
    print("  B = train and evaluate on test set (for teacher)")
    choice3 = input("Type A or B: ").strip().upper()
            
    
    df = load_data(train_path)
    runs = [] #varies per choice on test set
    
    if choice3 == "B":
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
    
    #init all options for the models to None and empty dictionary
    trained_models = {}
    active_extractor = None
    current_model_type = None
    
    for split_name, split_train, split_test in runs: #loop through classifiers to run
        for current_model_type in model_types_to_run: #loop through feature extractors
            trained_models.clear() #clears the models from the previous iteration 
        
            if current_model_type =='tfidf' :
                X_train_features, active_extractor = train_tfidf_vectorizer(split_train['utterance'])
                #the following makes sure new words are ignored that were not in the training set.
                #This means out of vocabulary words (OOV) are droppped! --> have to discuss this in report
                X_test_features = active_extractor.transform(split_test['utterance']) 
            elif current_model_type == 'distilbert': #need embeddings instead of vectorizer
                X_train_features = get_embeddings(split_train['utterance'].tolist(), batch_size=32)
                X_test_features = get_embeddings(split_test['utterance'].tolist(), batch_size=32)
                active_extractor = None #no need for extractor
            
            y_train = split_train['label'] 
            
            #run all classifiers that are asked in the input of the user
            if "SVM" in classifiers_to_run:
                trained_models["SVM"] = train_SVM(X_train_features, y_train)
            if "Logistic Regression" in classifiers_to_run:
                trained_models["Logistic Regression"] = train_logistic_regression(X_train_features, y_train)

            #save the models from the original split for later testing the dialogue
            if split_name == "original split (85/15)":
                os.makedirs("saved_models", exist_ok=True)

                for classifier, model in trained_models.items():
                    filename = (
                        f"original_{current_model_type}_"
                        f"{classifier.lower().replace(' ', '_')}.joblib"
                    )

                    joblib.dump(
                        {
                            "model": model,
                            "extractor": active_extractor,
                            "model_type": current_model_type,
                        },
                        os.path.join("saved_models", filename),
                    )

            for classifier, model in trained_models.items(): #looks at all trained models and evaluates
                predictions = model.predict(X_test_features) 
                evaluation = f"{current_model_type.upper()} + {classifier} ({split_name})"
                evaluate_test(split_test['label'], predictions, evaluation) #use evaluation on the trained models
            
    if choice3 != "B":
        print("\nEnter A to classify utterances "
                "or B if you want to run the restaurant dialogue")
        mode = input("Type A or B:").strip().upper()
        if mode == "B":
            if "SVM" in trained_models:
                user_selected_model = trained_models["SVM"]
            else: user_selected_model = trained_models["Logistic Regression"]
            interactive_dialogue(user_selected_model, active_extractor, current_model_type)
        else:
            interactive(trained_models, active_extractor, current_model_type) #so that the user can input an utterance

if __name__ == "__main__": 
    parser = argparse.ArgumentParser(description="Pipeline classifier of the dialog act")
    
    parser.add_argument(
        "--train_data", 
        type=str, 
        default=TRAIN_DATA_PATH,
    )
    
    parser.add_argument(
        "--test_data", 
        type=str, 
        default= TEST_DATA_PATH,
    )

    parser.add_argument(
        "--dialogue-only",
        action="store_true",
        help="Load a saved model and start the dialogue without training",
    )

    args = parser.parse_args()
    main(args.train_data, args.test_data, args.dialogue_only)