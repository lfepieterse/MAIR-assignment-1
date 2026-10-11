# MAIR-assignment-1

run for dependencies --> pip install -r requirements.txt

To test the held-out test data:
    In main, replace the TEST_DATA_PATH if the current one is not correct. When running main, choose C, C, B respectively if you want to run all models on the test data. The results will be stored in the evaluation_results.txt file in the results directory.

To have a dialogue with the system:
    choose the preferred models in the first choices, but after choosing A for choice 3, choose B to have a conversation. You can quit the conversation at any time by typing "quit"

You get 5 choices when running the main. In these choices you can decide
- the feature extraction method
- which classifier
- if want to use dev set or test set --> So for grader: choose B in the third choice for test set
At the end of training, you can give an input utterance
- if the previous choice was A (train and evaluate on local validation), the next choice is for a conversation. Either A classifying utterances or B run the restaurant dialogue
- If the previous choice was B: you can choose whether you want reasoning transperancy: yes or no

The results for the dev training are already stored in evaluation_results.txt

TRAINING:
To start the restaurant dialogue using a previously saved model without repeating the full training and evaluation pipeline, run: python main.py --dialogue-only
Choose the feature extraction method and classifier you want to use. The system loads the corresponding saved model and starts the interactive dialogue. For the restaurant recommendation dialogue of part 1b, we recommend using SVM with DistilBERT because it's performance proved best in pasr 1a of the assignment, but we justified this further in the report so please read about it further there.

reasoning component:
reasoning.py

Applies six rules to infer additional restaurant properties, such as whether a restaurant is touristic, has assigned seating, is suitable for children, or is romantic. It stores explanations for triggered rules and detects conflicting conclusions, which are returned to the dialogue manager for handling.

REASONING TRANPARANCY:
When starting the restaurant, the system asks the user whether reasoning should be provided in its response for which the user can type "yes" or "no". The restaurant extraction stays the same, only reasoning is added if "yes" is chosen for this. "show_reasoning" stores the setting while the response is build in the function "response_for_recommendation()"