import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import accuracy_score, f1_score
import time
import os

# =========================
# CONFIG
# =========================
BATCH_SIZE = 4096
EPOCHS = 20
LEARNING_RATE = 0.001
MODEL_SAVE_PATH = "model/cic_pytorch_model.pth"

# =========================
# DEVICE
# =========================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)

# =========================
# LOAD DATA
# =========================
X_train = torch.load("processed/X_train.pt")
X_test  = torch.load("processed/X_test.pt")
y_train = torch.load("processed/y_train.pt")
y_test  = torch.load("processed/y_test.pt")

num_features = X_train.shape[1]
num_classes = len(torch.unique(y_train))

train_dataset = TensorDataset(X_train, y_train)
test_dataset  = TensorDataset(X_test, y_test)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
test_loader  = DataLoader(test_dataset, batch_size=BATCH_SIZE)

# =========================
# MODEL
# =========================
class IDSModel(nn.Module):
    def __init__(self, input_size, num_classes):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(input_size, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(0.3),

            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.3),

            nn.Linear(256, 128),
            nn.ReLU(),

            nn.Linear(128, num_classes)
        )

    def forward(self, x):
        return self.model(x)

model = IDSModel(num_features, num_classes).to(device)

# =========================
# LOSS & OPTIMIZER
# =========================
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

# =========================
# TRAINING LOOP
# =========================
print("🔥 Training Started...")
start_time = time.time()

for epoch in range(EPOCHS):
    model.train()
    running_loss = 0

    for X_batch, y_batch in train_loader:
        X_batch = X_batch.to(device)
        y_batch = y_batch.to(device)

        optimizer.zero_grad()
        outputs = model(X_batch)
        loss = criterion(outputs, y_batch)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()

    print(f"Epoch [{epoch+1}/{EPOCHS}] Loss: {running_loss:.4f}")

end_time = time.time()
print(f"✅ Training Complete in {end_time - start_time:.2f} seconds")

# =========================
# EVALUATION
# =========================
model.eval()
all_preds = []
all_labels = []

with torch.no_grad():
    for X_batch, y_batch in test_loader:
        X_batch = X_batch.to(device)
        y_batch = y_batch.to(device)

        outputs = model(X_batch)
        _, predicted = torch.max(outputs, 1)

        all_preds.extend(predicted.cpu().numpy())
        all_labels.extend(y_batch.cpu().numpy())

accuracy = accuracy_score(all_labels, all_preds)
f1 = f1_score(all_labels, all_preds, average="weighted")

print(f"🎯 Test Accuracy: {accuracy:.4f}")
print(f"🎯 Weighted F1 Score: {f1:.4f}")

# =========================
# SAVE MODEL
# =========================
os.makedirs("model", exist_ok=True)
torch.save(model.state_dict(), MODEL_SAVE_PATH)

print(f"💾 Model saved to {MODEL_SAVE_PATH}")