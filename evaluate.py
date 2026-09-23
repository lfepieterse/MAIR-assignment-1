import os
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report

#Saves accuracy, balanced accuracy and classification report for the models and saves them 
def evaluate_test(y_true, y_pred, which_model = 'Model'):
    output_directory = "./results"
    output_file = f"{output_directory}/evaluation_results.txt"
    
    accuracy = accuracy_score(y_true, y_pred)
    balanced_accuracy = balanced_accuracy_score(y_true, y_pred)
    
    analysis_report = classification_report(y_true, y_pred, zero_division=0)
    
    print(which_model)
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Balanced Accuracy: {balanced_accuracy:.4f}")
    
    #if directory exists already it will not make it a second time
    os.makedirs(output_directory, exist_ok=True)
    
    already_saved = False #check if a specific header is saved already to avoid duplicates
    header_text = f"Evaluation of {which_model}"
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            if header_text in f.read():
                already_saved = True
    
    if not already_saved:
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(f"Evaluation of {which_model} \n")
            f.write(f"Accuracy: {accuracy:.4f}\n")
            f.write(f"Balanced Accuracy: {balanced_accuracy:.4f}\n")
            f.write("Report of the classification:\n")
            f.write(analysis_report)
            f.write("\n" + "="*50 + "\n\n")
        
    print("done, see output file!")