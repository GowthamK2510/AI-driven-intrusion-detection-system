import pandas as pd
import numpy as np
import torch
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
import os

# =========================
# CONFIG
# =========================
DATA_PATH = "cic_ids_2018.csv"   # change to your CSV file
SAVE_DIR = "processed"
TEST_SIZE = 0.2
RANDOM_STATE = 42

os.makedirs(SAVE_DIR, exist_ok=True)

print("Loading dataset...")
df = pd.read_csv(DATA_PATH, low_memory=False)

# =========================
# CLEAN COLUMN NAMES
# =========================
df.columns = df.columns.str.strip()

# =========================
# REMOVE INVALID VALUES
# =========================
df.replace([np.inf, -np.inf], np.nan, inplace=True)
df.dropna(inplace=True)

print("Dataset shape after cleaning:", df.shape)

# =========================
# GROUP LABELS
# =========================
def map_labels(label):
    label = label.lower()
    
    if "benign" in label:
        return "Benign"
    elif "ddos" in label:
        return "DDoS"
    elif "dos" in label:
        return "DoS"
    elif "brute" in label:
        return "BruteForce"
    elif "bot" in label:
        return "Bot"
    elif "web" in label:
        return "WebAttack"
    elif "infiltration" in label:
        return "Infiltration"
    else:
        return "Other"

df["Label"] = df["Label"].apply(map_labels)

# Remove rare/Other if exists
df = df[df["Label"] != "Other"]

print("Label distribution:")
print(df["Label"].value_counts())

# =========================
# SPLIT FEATURES & LABEL
# =========================
X = df.drop("Label", axis=1)
y = df["Label"]

# =========================
# ENCODE LABELS
# =========================
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# Save label classes
np.save(os.path.join(SAVE_DIR, "classes.npy"), le.classes_)

# =========================
# SCALE FEATURES
# =========================
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# =========================
# TRAIN-TEST SPLIT
# =========================
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y_encoded,
    test_size=TEST_SIZE,
    stratify=y_encoded,
    random_state=RANDOM_STATE
)

# =========================
# CONVERT TO TORCH TENSORS
# =========================
X_train_tensor = torch.tensor(X_train, dtype=torch.float32)
X_test_tensor  = torch.tensor(X_test, dtype=torch.float32)
y_train_tensor = torch.tensor(y_train, dtype=torch.long)
y_test_tensor  = torch.tensor(y_test, dtype=torch.long)

# =========================
# SAVE TENSORS
# =========================
torch.save(X_train_tensor, os.path.join(SAVE_DIR, "X_train.pt"))
torch.save(X_test_tensor, os.path.join(SAVE_DIR, "X_test.pt"))
torch.save(y_train_tensor, os.path.join(SAVE_DIR, "y_train.pt"))
torch.save(y_test_tensor, os.path.join(SAVE_DIR, "y_test.pt"))

print("Preprocessing completed successfully.")
print("Saved to folder:", SAVE_DIR)