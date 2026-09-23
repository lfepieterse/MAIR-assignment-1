# Imports
import time
import numpy as py
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.model_selection import train_test_split, StratifiedGroupKFold
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, balanced_accuracy_score
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd



# Data Loading and converting to lowercase
def load_data(path_data):
    data = []
    with open(path_data, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue

            label_and_utterance = line.split(" ", 1) #only split by the first space because this is the lable and utterance split
            label, utterance = label_and_utterance[0], label_and_utterance[1].lower() #convert utterance to lowercase
            data.append((label, utterance))

    return pd.DataFrame(data, columns=['label', 'utterance'])

#Data splitting

#original split
#sklearn for splitting the original data. Use stratify so that the train and test data have the same label proportions
def create_original_split(df):
    train, test = train_test_split(df, test_size=0.15, train_size =0.85, random_state=0, stratify=df['label'])
    print(f"Original Split - Train: {len(train)}, Test: {len(test)}")
    return train, test

#Grouped split
def create_grouped_split(df):
    df_grouped = df.drop_duplicates(subset=['utterance']) #make dataset where all duplicates of utterances are removed
    #if there is one instance of an utterance we have to manually add this later because we have to stratify the data
    class_countings = df_grouped['label'].value_counts()
    one_instance_classes = class_countings[class_countings < 2].index.tolist()
    #now make 2 parts of the data: the normal part that we will split and the classes that we can not split beacuse only one instance
    df_one_instance = df_grouped[df_grouped['label'].isin(one_instance_classes)]
    df_rest = df_grouped[~df_grouped['label'].isin(one_instance_classes)]

    #same as for original split but with non-repeated utterances, and not for the single instances
    train_rest, test_unique = train_test_split(df_rest, test_size=0.15, train_size =0.85, random_state=0, stratify=df_rest['label'])
    train_unique = pd.concat([train_rest, df_one_instance]) #adds the one instances cases to the training set so the models can learn from it

    # get the grouped split by putting all formerly removed duplicates back in the set (group/train) where its duplicates are split into
    train_grouped = df[df['utterance'].isin(train_unique['utterance'])]
    test_grouped = df[df['utterance'].isin(test_unique['utterance'])]


    print(f"Grouped Split - Train: {len(train_grouped)}, Test: {len(test_grouped)}")
    return train_grouped, test_grouped