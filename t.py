import pandas as pd
import numpy as np
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import StandardScaler
import joblib

CHUNK_SIZE = 200000
FILE_PATH = "cicids2018.csv"

print("🚀 Training in memory-safe chunks...")

# ---- First, detect all possible classes safely ----
print("Scanning file once to detect classes...")

label_samples = []

for chunk in pd.read_csv(FILE_PATH, chunksize=CHUNK_SIZE):
    label_col = [c for c in chunk.columns if "label" in c.lower()][0]
    label_samples.extend(chunk[label_col].unique())
    if len(set(label_samples)) > 1:
        break

classes = np.unique(label_samples)
print("Detected classes:", classes)

# ---- Initialize model ----
model = SGDClassifier(loss="log_loss")
scaler = StandardScaler()

first_chunk = True

# ---- Train in chunks ----
for chunk in pd.read_csv(FILE_PATH, chunksize=CHUNK_SIZE):

    chunk = chunk.replace([np.inf, -np.inf], np.nan)
    chunk = chunk.fillna(0)

    label_col = [c for c in chunk.columns if "label" in c.lower()][0]

    X = chunk.drop(columns=[label_col])
    y = chunk[label_col]

    X = X.apply(pd.to_numeric, errors="coerce").fillna(0)

    if first_chunk:
        scaler.fit(X)
        X = scaler.transform(X)
        model.partial_fit(X, y, classes=classes)
        first_chunk = False
    else:
        X = scaler.transform(X)
        model.partial_fit(X, y)

    print("Processed chunk...")

joblib.dump(model, "cicids_model.pkl")
joblib.dump(scaler, "scaler.pkl")

print("✅ Training complete and model saved.")