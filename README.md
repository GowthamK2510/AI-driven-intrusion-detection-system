# AI-Driven Intrusion Detection System

An advanced Intrusion Detection System (IDS) powered by supervised machine learning models. This repository contains the data preprocessing, model training, and evaluation pipelines for detecting network anomalies and malicious activities.

## Features

- **Multi-Dataset Support**: Built to train and evaluate on robust benchmark datasets including **CIC-IDS-2018** and **UNSW-NB15**.
- **Data Preprocessing**: Dedicated preprocessing scripts (`preprocessing_cicids2018.py`, `preprocessing_unsw.py`, `data_preprocessing.py`) to handle raw network captures and format them for ML consumption.
- **Model Training Pipelines**: Multiple training implementations, including PyTorch-based training and GPU-optimized training (`train_cic_pytorch.py`, `train_gpu_optimized.py`).
- **Live Capabilities**: Includes a network scanner component (`ns.py`) and API key detection logic (`api_key_detector.py`).

## Project Structure

- `data_preprocessing.py` / `preprocessing_*.py`: Scripts for cleaning, normalizing, and encoding the raw datasets.
- `train_*.py`: Model training scripts for different datasets and frameworks (PyTorch, standard machine learning).
- `ns.py`: Network scanning and live detection module.
- `api_key_detector.py`: Scans traffic or logs for exposed API keys.
- `setup.py`: Project installation and configuration setup.
- `.gitignore`: Configured to ignore large datasets (like `*.csv`, `*.pkl`) and virtual environments to adhere to GitHub's file size limits.

## Getting Started

### Prerequisites

Ensure you have Python 3.8+ installed. It is recommended to use a virtual environment.

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # On Windows
```

*(Note: You will need to download the CIC-IDS-2018 or UNSW-NB15 datasets manually and place them in the project directory, as they are too large for version control.)*

## Usage

1. **Preprocess Data**: Run the respective preprocessing script for your target dataset.
2. **Train Model**: Execute one of the training files (e.g., `python train_gpu_optimized.py`) to build the classification model.
3. **Scan Network**: Use `python ns.py` to initiate the network scanning features.

## License

This project is for educational and research purposes.
