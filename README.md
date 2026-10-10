# MAIR-assignment-1

run for dependencies --> pip install -r requirements.txt

To test the held-out test data:
    In main, replace the TEST_DATA_PATH if the current one is not correct. When running main, choose C, C, B respectively if you want to run all models on the test data. The results will be stored in the evaluation_results.txt file in the results directory.

To have a dialogue with the system:
    choose the preferred models in the first choices, but after choosing A for choice 3, choose B to have a conversation. You can quit the conversation at any time by typing "quit"

You get 4 choices when running the main. In these choices you can decide
- the feature extraction method
- which classifier
- if want to use dev set or test set --> So for grader: choose B in the third choice for test set
At the end of training, you can give an input utterance
- if the previous choice was A (train and evaluate on local validation), the next choice is for a conversation. Either A classifying utterances or B run the restaurant dialogueod

The results for the dev training are already stored in evaluation_results.txt