import os
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# Import from your NEW preprocessing file
from preprocessing_unsw import load_data, preprocess

# 1. Load Data
print("Loading UNSW-NB15 Dataset...")
df = load_data("UNSW_NB15_training-set.csv")  # <--- Make sure filename matches exactly!

# 2. Preprocess
X, y, preprocessor = preprocess(df)

# 3. Split Data (Train on 80%, Test on 20%)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. Define Model (Random Forest)
model = RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=42)

# 5. Create Pipeline
pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('classifier', model)
])

# 6. Train
print("Training Model 2 (UNSW Specialist)... this might take a minute...")
pipeline.fit(X_train, y_train)

# 7. Evaluate
print("Evaluating...")
y_pred = pipeline.predict(X_test)
print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
print(classification_report(y_test, y_pred))

# 8. Save
if not os.path.exists('model'):
    os.makedirs('model')

joblib.dump(pipeline, "model/ids_model_unsw.pkl")
print("✅ Model 2 Saved: model/ids_model_unsw.pkl")