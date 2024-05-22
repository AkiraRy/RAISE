import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC

from sklearn.metrics import accuracy_score, classification_report

#
# train_df = pd.read_csv("training_data.csv")
# val_df = pd.read_csv("validation_data.csv")
#
# # Extract queries and labels from the dataframes
# train_queries = train_df['query']
# train_labels = train_df['label']
#
# val_queries = val_df['query']
# val_labels = val_df['label']
#
# print('Removing data duplicates in training...')
# unique_train_queries = set()
# unique_train_data = []
# for query, label in zip(train_queries, train_labels):
#     if query not in unique_train_queries:
#         unique_train_queries.add(query)
#         unique_train_data.append((query, label))
# train_queries = [query for query, _ in unique_train_data]
# train_labels = [label for _, label in unique_train_data]
#
# print('Removing data duplicates in validation...')
# unique_val_queries = set()
# unique_val_data = []
# for query, label in zip(val_queries, val_labels):
#     if query not in unique_val_queries:
#         unique_val_queries.add(query)
#         unique_val_data.append((query, label))
# val_queries = [query for query, _ in unique_val_data]
# val_labels = [label for _, label in unique_val_data]
#
# unique_train_queries = set(train_queries)
# unique_val_queries = set(val_queries)
#
# # Find common queries between training and validation data
# common_queries = unique_train_queries.intersection(unique_val_queries)
# print('Checking for data contamination...')
# if len(common_queries) > 0:
#     print("Warning: Training data leaked into validation data!")
#     print("Common Queries:")
#     for query in common_queries:
#         print(query)
#
#     val_queries_cleaned = [query for query in val_queries if query not in common_queries]
#     val_labels_cleaned = [label for query, label in zip(val_queries, val_labels) if query not in common_queries]
#
#     val_queries = val_queries_cleaned
#     val_labels = val_labels_cleaned
#
#     print("Validation data has been cleaned.")
# else:
#     print("No training data leaked into validation data.")
#
# # Vectorize the text using TF-IDF
# vectorizer = TfidfVectorizer()
# train_vectors = vectorizer.fit_transform(train_queries)
# val_vectors = vectorizer.transform(val_queries)
#
# # SVC
# svm_classifier = SVC(kernel='linear', probability=True, random_state=42)
# svm_classifier.fit(train_vectors, train_labels)
# svm_predictions = svm_classifier.predict(val_vectors)
#
# # Train Random Forest classifier
# # rf_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
# # rf_classifier.fit(train_vectors, train_labels)
# # rf_predictions = rf_classifier.predict(val_vectors)
#
# accuracy_RF = accuracy_score(val_labels,svm_predictions)
# print(f"Validation Accuracy: {accuracy_RF:.2%}")
#
# model_filename = 'svm_classifier_model.pkl'
# joblib.dump(svm_classifier, model_filename)
# # vectorizer_filename = 'tfidf_vectorizer.pkl'
# # joblib.dump(vectorizer, vectorizer_filename)
#
# print('Done! Trained models saved.')


def predict_module(query, vectorizer, loaded_model):
    query_vector = vectorizer.transform([query])
    predictions = loaded_model.predict(query_vector)
    predicted_probabilities = loaded_model.predict_proba(query_vector)
    # if max(predicted_probabilities[0]) < 0.9:
    #     return None, max(predicted_probabilities[0])
    return predictions[0], max(predicted_probabilities[0])

if __name__ == "__main__":
    # labels i can have for detection
    """
    Home assistant  (maybe break it down even more? or have another which will determine what to do)
    Weather 
    
    """

    "bayes the worst? depend on dataset, then rf , svm"
    query = "How much does the car cost?"

    vectorizer_filename = f'tfidf_vectorizer.pkl'
    vectorizer = joblib.load(vectorizer_filename)

    rf = f'random_forest_model.pkl'
    svm = f'svm_classifier_model.pkl'
    nb = f'naive_bayes_model.pkl'

    loaded_rf = joblib.load(rf)
    loaded_svm = joblib.load(svm)
    loaded_nb = joblib.load(nb)

    prediction = predict_module(query, vectorizer, loaded_rf)
    prediction_1 = predict_module(query, vectorizer, loaded_nb)
    prediction_2 = predict_module(query, vectorizer, loaded_svm)

    print(f"RF:  {prediction[0]}, {prediction[1]:.2f}")
    print(f"NB:  {prediction_1[0]}, {prediction_1[1]:.2f}")
    print(f"SVM:{prediction_2[0]}, {prediction_2[1]:.2f}")



