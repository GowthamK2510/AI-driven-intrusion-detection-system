from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
import joblib
from data_preprocessing import load_data, preprocess
'''data/KDDTrain+.txt'''
'''df = load_data("data/KDDTrain+.txt")
pipeline = Pipeline([
    ("preprocessing", preprocessor),
    ("classifier", model)
])

X, y, preprocessor = preprocess(df)

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=None,
    random_state=42,
    n_jobs=-1
)



pipeline.fit(X, y)

joblib.dump(pipeline, "model/ids_model.pkl")
print("Model trained and saved.")'''
from data_preprocessing import load_data, preprocess
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

df = load_data("data/KDDTrain+.txt")

X, y, preprocessor = preprocess(df)

# Apply preprocessing
X = preprocessor.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = RandomForestClassifier(n_estimators=100)

model.fit(X_train, y_train)

print("Training completed.")
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

y_pred = model.predict(X_test)

print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nConfusion Matrix:\n", confusion_matrix(y_test, y_pred))
print("\nClassification Report:\n", classification_report(y_test, y_pred))
# --- ADD THIS AT THE END ---
from sklearn.pipeline import Pipeline
import joblib

# 1. We must combine your 'preprocessor' and 'model' into a 'pipeline' variable
# (The computer needs this definition before it can save it)
pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('classifier', model)
])

# 2. NOW we can save it
joblib.dump(pipeline, "model/ids_model.pkl")
print("✅ Saved successfully!")
