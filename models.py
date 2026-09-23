import numpy as np
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from transformers import DistilBertTokenizer, DistilBertModel


# Rule Based Baseline

def rule_based_classifying(utterance):
  #dictionary of label and keywords we found are common for that label (see previous code snippet)
  rules = {

        "inform": ["any", "west", "south", "north", "east", "dont care", "expensive"], #or else
        "thankyou": ["thank", "thanks", "thank you good bye", "thank you goodbye"],
        "bye": ["goodbye", "bye", "later"],
        "deny": ["not", "wrong"],
        "hello": ["hello", "hi"],
        "repeat": ["repeat", "back"],
        "reqalts": ["anything else", "how about", "what about", "another option", "is there"], #1.635
        "reqmore": ["more"],
        "request": ["what", "whats", "what is", "can I have", "adress", "may I", "code", "number", "price range", "get", "could I", "is it"],
        "confirm": ["correct", "that is right", "is it","does it"],
        "negate": ["no"] ,
        "restart": ["start over", "start again", "restart", "try"],
        "ack": ["okay", "good", "kay"],
        "affirm": ["yes right", "right", "yes", "yea", "ye"],
        "null": ["noise","um", "unintelligible", "sil", "cough", "static", "laugh", "blow"] #komt heel vaak voor
  }

  #iterate through the keywords, and if the keyword is in the utterance, return that class label
  for label, keywords in rules.items():
        for keyword in keywords:
            if keyword in utterance:
                return label

  # If no keywords match, inform is very redundant in data
  return "inform"
"""
# Evaluate baseline
baseline = test['utterance'].apply(rule_based_classifying)
print("Baseline Accuracy:", accuracy_score(test['label'], baseline))

#extra evaluation (balanced accuracy)
print("Baseline Balanced Accuracy:",
      balanced_accuracy_score(test['label'], baseline))"""
      
      
# TF IDF (Term Frequency–Inverse Document Frequency) representation for random 85/15 split
#gives a numerical value to words based on:
#amount of times a word occurs in a single utterance
#how common a word is across all utterances
def train_tfidf_vectorizer(train_utterances):
    #numerical representation of training utterances
    vectorizer = TfidfVectorizer()

    #look through the training utterances and learns the 
    # vocabulary and the statistics for the TF-IDF--> 
    # convert every training utterance into a vector
    X_train = vectorizer.fit_transform(train_utterances)
    return X_train, vectorizer

def train_logistic_regression(X_train, y_train):
    #create the logistic regression model (with max number of 
    # iterations the algorithm can use for training)
    model = LogisticRegression(max_iter=1000)
    #fit data (which features are associated with which 
    # dialog-act classes) 
    model.fit(X_train, y_train) 
    return model

def train_SVM(X_train, y_train):
    model = LinearSVC() #create the svm
    model.fit(X_train, y_train) #train the svm
    return model


#DistilBERT
#turn text into numbers in format for DistilBERT
tokenizer = DistilBertTokenizer.from_pretrained(
    "distilbert-base-uncased"
)
#processes token IDs and output numerical representations with info about the text
model = DistilBertModel.from_pretrained(
    "distilbert-base-uncased"
)

def get_embedding(text):
    encoded_input = tokenizer(
        text,
        return_tensors='pt'
    )

    with torch.no_grad():
        output = model(**encoded_input)

    embedding = output.last_hidden_state.mean(dim=1)

    return embedding.squeeze().numpy()