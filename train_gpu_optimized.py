import pandas as pd
import numpy as np
import time
import joblib
import os
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# =========================
# SETTINGS
# =========================
FILE_PATH = "cic_ids_2018.csv"
MODEL_PATH = "model/ids_model_cic_gpu.pkl"
ROW_LIMIT = 200000

print("🚀 Starting Memory-Safe GPU Training...")

# =========================
# STEP 1: LOAD DATA (FIXED PARSING)
# =========================
print("📥 Loading data safely...")
try:
    # We add on_bad_lines='skip' to drop malformed rows instead of breaking the columns
    df = pd.read_csv(
        FILE_PATH,
        nrows=ROW_LIMIT,
        low_memory=False,
        on_bad_lines='skip', 
        engine="c"
    )
    
    df.columns = df.columns.str.strip()
    
    # Dynamically find target column
    target_col = "Label" if "Label" in df.columns else df.columns[-1]
    print(f"🎯 Target Column Detected: {target_col}")
    print(f"✅ Loaded {len(df)} rows and {len(df.columns)} columns.")

except Exception as e:
    print(f"❌ Error loading file: {e}")
    exit()

# =========================
# STEP 2: CLEAN DATA (NO DROPPING ROWS)
# =========================
print("🛠️ Cleaning and preprocessing...")

# Drop obvious non-feature columns
drop_cols = [col for col in df.columns if any(x in col.lower() for x in ["flow id", "source ip", "destination ip", "timestamp"])]

if drop_cols:
    print(f"Dropping {len(drop_cols)} non-feature columns...")
    df.drop(columns=drop_cols, inplace=True)

# Separate features and label
X = df.drop(columns=[target_col])
y = df[target_col]

# Convert features to numeric, forcing errors to NaN
X = X.apply(pd.to_numeric, errors="coerce")

# Replace infinity with NaN
X.replace([np.inf, -np.inf], np.nan, inplace=True)

# ⚠️ CRITICAL FIX: Do NOT use X.dropna() here. It deletes rows.
# Instead, drop columns that are 100% empty, then fill the rest with 0.
X.dropna(axis=1, how='all', inplace=True)
X.fillna(0, inplace=True)

print(f"📊 Dataset after cleaning: {X.shape}")

# Encode target
le_target = LabelEncoder()
y = le_target.fit_transform(y.astype(str))

os.makedirs("model", exist_ok=True)
joblib.dump(le_target, "model/cic_label_encoder.pkl")
# =========================
# STEP 3: TRAIN TEST SPLIT
# =========================
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print(f"Train size: {len(X_train)}")
print(f"Test size: {len(X_test)}")

# =========================
# STEP 4: GPU MODEL (UPDATED)
# =========================
print("⚡ Initializing XGBoost on NVIDIA GPU...")

# Use device="cuda" for XGBoost >= 2.0
model = XGBClassifier(
    n_estimators=100,
    learning_rate=0.1,
    max_depth=8,
    tree_method="hist",      # 'hist' is the standard method now
    device="cuda",           # This forces the model onto the GPU
    objective="multi:softmax",
    num_class=len(np.unique(y)),
    eval_metric="mlogloss",
    verbosity=1
)

# =========================
# STEP 5: TRAIN
# =========================
print("🔥 Training Started...")
print("👉 Run 'nvidia-smi -l 1' in another terminal to verify GPU usage")

start_time = time.time()
model.fit(X_train, y_train)
end_time = time.time()

print(f"✅ Training Complete in {end_time - start_time:.2f} seconds")

# =========================
# STEP 6: SAVE MODEL
# =========================
joblib.dump(model, MODEL_PATH)
print(f"💾 Model saved to {MODEL_PATH}")