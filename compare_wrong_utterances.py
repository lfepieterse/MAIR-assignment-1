from pathlib import Path
import pandas as pd

# comparing the grouped result files with wrongly classified utterances
files_grouped = [
    "results/errors_grouped_tfidf_svm.csv",
    "results/errors_grouped_tfidf_logistic_regression.csv",
    "results/errors_grouped_distilbert_svm.csv",
    "results/errors_grouped_distilbert_logistic_regression.csv",
]
counts_grouped = {}

for file in files_grouped:
    errors = pd.read_csv(file, keep_default_na=False)
    #count every pair only once
    errors = errors.drop_duplicates(subset=["utterance", "label"])
    
    for _, row in errors.iterrows():
        utterance_example = (row["utterance"], row["label"])

        if utterance_example not in counts_grouped:
            counts_grouped[utterance_example] = 0

        counts_grouped[utterance_example] += 1

#if wrong for all four configurations of grouped, print
for example, number in counts_grouped.items():
    if number == 4:
        utterance, label = example
        print(f"utterance = {utterance}")
        print(f"true label = {label}")



#same for original
files_original = [
    "results/errors_original_tfidf_svm.csv",
    "results/errors_original_tfidf_logistic_regression.csv",
    "results/errors_original_distilbert_svm.csv",
    "results/errors_original_distilbert_logistic_regression.csv",
]
counts_original = {}

for file in files_original:
    errors = pd.read_csv(file, keep_default_na=False)
    #count every pair only once
    errors = errors.drop_duplicates(subset=["utterance", "label"])
    
    for _, row in errors.iterrows():
        utterance_example = (row["utterance"], row["label"])

        if utterance_example not in counts_original:
            counts_original[utterance_example] = 0

        counts_original[utterance_example] += 1

for example, number in counts_original.items():
    if number == 4:
        utterance, label = example
        print(f"utterance = {utterance}")
        print(f"true label = {label}")



