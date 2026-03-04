"""Small training scripts for LSTM and DBSCAN (demo mode).

This script uses the project's synthetic data generators to train models
locally for development/testing. For production/historical training you
should provide real datasets and configure proper training infra.
"""
import os
import pickle
from app.ml.lstm_model import lstm_predictor
from app.ml.dbscan_model import dbscan_segmentation


def train_lstm(epochs: int = 3):
    print("[train] Generating synthetic data for LSTM...")
    data = lstm_predictor.generate_synthetic_data(num_samples=2000)
    print(f"[train] Training LSTM for {epochs} epochs (demo)...")
    history = lstm_predictor.train(data, epochs=epochs)
    print("[train] LSTM training complete. Model saved to:", lstm_predictor.model_path)
    return history


def train_dbscan():
    print("[train] Generating synthetic users for DBSCAN...")
    users = dbscan_segmentation.generate_synthetic_users(num_users=500)
    print("[train] Fitting DBSCAN (demo)...")
    res = dbscan_segmentation.fit(users)
    os.makedirs('models', exist_ok=True)
    dbscan_path = os.path.join('models', 'dbscan_segmentation.pkl')
    with open(dbscan_path, 'wb') as f:
        pickle.dump(dbscan_segmentation, f)
    print(f"[train] DBSCAN model object saved to: {dbscan_path}")
    return res


if __name__ == '__main__':
    # Small demo run
    train_lstm(epochs=2)
    train_dbscan()
