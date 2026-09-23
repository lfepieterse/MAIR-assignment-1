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
model.eval()


#processing all utterances in batches of size 32
def get_embeddings(texts, batch_size=32):
    embeddings = []

    #loop through utterances in batch_size steps
    for i in range(0, len(texts), batch_size):

        #take a batch of utterances
        batch = texts[i:i + batch_size]

        #convert the batch (from text into tokens)
        #padding=True makes the sequences in the batch the same length
        #truncation=True prevents sequences from being too long
        encoded_input = tokenizer(
            batch,
            padding=True,
            truncation=True,
            return_tensors='pt'
        )

        #get distilBERT output
        with torch.no_grad():
            output = model(**encoded_input)

        #get the token embeddings
        token_embeddings = output.last_hidden_state

        #get attention mask: 1 for real tokens and 0 for padding tokens
        #also another dimension added so it can be multiplied with the token embeddings
        attention_mask = encoded_input['attention_mask'].unsqueeze(-1)

        #ignore padding tokens for computation of the average
        #set the padding token representations to 0 so they are not included when computing the average
        masked_embeddings = token_embeddings * attention_mask

        #sum embeddings of the real tokens
        sum_embeddings = masked_embeddings.sum(dim=1)

        #count amount of real tokens for each sentence
        sum_mask = attention_mask.sum(dim=1)

        #avg the token embeddings
        batch_embeddings = sum_embeddings / sum_mask

        #convert to numpy & store this batch
        embeddings.append(batch_embeddings.numpy())

    #all batches into 1 big array
    return np.vstack(embeddings)