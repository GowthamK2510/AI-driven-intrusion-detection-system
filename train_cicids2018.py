import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import numpy as np

# ========== LOAD DATA (Memory Safe) ==========
print("Loading processed data...")
X = np.load("X.npy", mmap_mode='r')
y = np.load("y.npy", mmap_mode='r')

# ========== DATASET CLASS ==========
class CICDataset(Dataset):
    def __init__(self, X, y):
        self.X = X
        self.y = y

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return torch.tensor(self.X[idx]), torch.tensor(self.y[idx])

dataset = CICDataset(X, y)

train_loader = DataLoader(
    dataset,
    batch_size=256,
    shuffle=True,
    num_workers=2,
    pin_memory=True
)

# ========== GPU SETUP ==========
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)

# ========== MODEL ==========
class IDSModel(nn.Module):
    def __init__(self, input_dim, num_classes):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.BatchNorm1d(256),
            nn.Dropout(0.3),

            nn.Linear(256, 128),
            nn.ReLU(),
            nn.BatchNorm1d(128),

            nn.Linear(128, num_classes)
        )

    def forward(self, x):
        return self.net(x)

input_dim = X.shape[1]
num_classes = len(np.unique(y[:10000]))

model = IDSModel(input_dim, num_classes).to(device)

# ========== HANDLE CLASS IMBALANCE ==========
class_counts = np.bincount(y[:])
class_weights = 1. / torch.tensor(class_counts, dtype=torch.float)
criterion = nn.CrossEntropyLoss(weight=class_weights.to(device))

optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

# ========== TRAINING LOOP ==========
epochs = 15

for epoch in range(epochs):
    model.train()
    total_loss = 0

    for batch_X, batch_y in train_loader:
        batch_X = batch_X.to(device, non_blocking=True)
        batch_y = batch_y.to(device, non_blocking=True)

        optimizer.zero_grad()
        outputs = model(batch_X)
        loss = criterion(outputs, batch_y)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss:.4f}")

# ========== SAVE MODEL ==========
torch.save(model.state_dict(), "ids_model.pth")
print("Training complete. Model saved.")
