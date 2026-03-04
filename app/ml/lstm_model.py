"""
LSTM Demand Predictor para CityTransit
=======================================
Predicción de demanda de transporte usando redes LSTM.
Soporta entrenamiento, evaluación y predicción con fallback.
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error
import logging
import os
import json
import joblib
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from app.core.config import settings

# Optional TensorFlow import
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
    from tensorflow.keras.optimizers import Adam
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False
    tf = None

logger = logging.getLogger(__name__)

if not HAS_TENSORFLOW:
    logger.warning("⚠️ TensorFlow not available. Using fallback predictions.")


class LSTMDemandPredictor:
    """LSTM Model for demand prediction with full ML pipeline support"""
    
    # Features utilizadas para predicción
    FEATURES = [
        'hour', 'day_of_week', 'month', 'is_weekend', 'is_holiday',
        'temperature', 'precipitation', 'events_count', 'previous_demand', 'rolling_mean'
    ]
    
    def __init__(self, sequence_length: int = 24):
        self.model = None
        self.scaler = MinMaxScaler()
        self.target_scaler = MinMaxScaler()  # Scaler para target (demand)
        self.model_path = getattr(settings, 'LSTM_MODEL_PATH', 'models/lstm_demand_model.h5')
        self.scaler_path = getattr(settings, 'LSTM_SCALER_PATH', 'models/lstm_scaler.joblib')
        self.metadata_path = getattr(settings, 'LSTM_METADATA_PATH', 'models/lstm_metadata.json')
        self.sequence_length = sequence_length
        self.is_fitted = False
        self.training_history = None
        self.evaluation_metrics = None
        
    def build_model(self, input_shape: Tuple[int, int], 
                    units: List[int] = None,
                    dropout_rate: float = 0.2,
                    learning_rate: float = 0.001) -> Optional[Sequential]:
        """Build LSTM model with configurable architecture
        
        Args:
            input_shape: (sequence_length, num_features)
            units: List of LSTM units for each layer
            dropout_rate: Dropout rate between layers
            learning_rate: Learning rate for Adam optimizer
            
        Returns:
            Compiled Keras model or None if TensorFlow not available
        """
        if units is None:
            units = [128, 64, 32]
            
        if not HAS_TENSORFLOW:
            logger.warning("⚠️ TensorFlow not available. Cannot build LSTM model.")
            return None
        
        model = Sequential()
        
        # First LSTM layer
        model.add(LSTM(units[0], return_sequences=True, input_shape=input_shape))
        model.add(BatchNormalization())
        model.add(Dropout(dropout_rate))
        
        # Middle LSTM layers
        for i, unit in enumerate(units[1:-1], 1):
            model.add(LSTM(unit, return_sequences=True))
            model.add(BatchNormalization())
            model.add(Dropout(dropout_rate))
        
        # Last LSTM layer
        model.add(LSTM(units[-1], return_sequences=False))
        model.add(BatchNormalization())
        model.add(Dropout(dropout_rate))
        
        # Dense output layers
        model.add(Dense(16, activation='relu'))
        model.add(Dense(1))
        
        # Compile with Adam optimizer
        optimizer = Adam(learning_rate=learning_rate)
        model.compile(
            optimizer=optimizer,
            loss='mse',
            metrics=['mae', 'mape']
        )
        
        logger.info(f"✅ LSTM model built: {len(units)} LSTM layers, {sum(units)} total units")
        return model
    
    def load_or_create_model(self):
        """Load existing model or create new one"""
        if not HAS_TENSORFLOW:
            logger.warning("⚠️ TensorFlow not available. Using rule-based predictions.")
            self.model = None
            return None
        
        # Intentar cargar modelo completo (modelo + scaler + metadata)
        if os.path.exists(self.model_path):
            if self.load_model():
                return self.model
        
        # Si no se pudo cargar, crear nuevo modelo
        logger.info("📦 Creating new LSTM model...")
        self.model = self.build_model((self.sequence_length, len(self.FEATURES)))
        return self.model
    
    def prepare_data(self, data: pd.DataFrame, fit_scaler: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for LSTM with proper scaling
        
        Args:
            data: DataFrame with features and demand
            fit_scaler: If True, fit the scaler. If False, only transform
            
        Returns:
            Tuple of (X sequences, y targets)
        """
        # Validate features
        missing_features = [f for f in self.FEATURES if f not in data.columns]
        if missing_features:
            raise ValueError(f"Missing features: {missing_features}")
        
        if 'demand' not in data.columns:
            raise ValueError("Missing 'demand' column in data")
        
        # Scale features
        if fit_scaler:
            scaled_features = self.scaler.fit_transform(data[self.FEATURES])
            scaled_target = self.target_scaler.fit_transform(data[['demand']])
        else:
            scaled_features = self.scaler.transform(data[self.FEATURES])
            scaled_target = self.target_scaler.transform(data[['demand']])
        
        # Create sequences
        X, y = [], []
        for i in range(len(scaled_features) - self.sequence_length):
            X.append(scaled_features[i:i + self.sequence_length])
            y.append(scaled_target[i + self.sequence_length, 0])
        
        return np.array(X), np.array(y)
    
    def _get_callbacks(self, patience: int = 10) -> List:
        """Get training callbacks
        
        Args:
            patience: Patience for early stopping
            
        Returns:
            List of Keras callbacks
        """
        if not HAS_TENSORFLOW:
            return []
        
        # Ensure model directory exists
        os.makedirs(os.path.dirname(self.model_path) if os.path.dirname(self.model_path) else '.', exist_ok=True)
        
        callbacks = [
            # Early stopping to prevent overfitting
            EarlyStopping(
                monitor='val_loss',
                patience=patience,
                restore_best_weights=True,
                verbose=1
            ),
            # Save best model
            ModelCheckpoint(
                self.model_path,
                monitor='val_loss',
                save_best_only=True,
                verbose=0
            ),
            # Reduce learning rate on plateau
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=patience // 2,
                min_lr=1e-6,
                verbose=1
            )
        ]
        
        return callbacks
    
    def train(self, data: pd.DataFrame, 
              epochs: int = 100, 
              batch_size: int = 32,
              validation_split: float = 0.2,
              patience: int = 10,
              use_time_series_cv: bool = False,
              n_splits: int = 5) -> Dict[str, Any]:
        """Train LSTM model with callbacks and validation
        
        Args:
            data: DataFrame with training data
            epochs: Maximum number of epochs
            batch_size: Batch size for training
            validation_split: Fraction of data for validation
            patience: Early stopping patience
            use_time_series_cv: Use time series cross-validation
            n_splits: Number of splits for time series CV
            
        Returns:
            Dict with training history and metrics
        """
        if not HAS_TENSORFLOW:
            logger.warning("⚠️ TensorFlow not available. Cannot train model.")
            return {'error': 'TensorFlow not available'}
        
        logger.info("🤖 Training LSTM model...")
        start_time = datetime.now()
        
        X, y = self.prepare_data(data, fit_scaler=True)
        
        if self.model is None:
            self.model = self.build_model((X.shape[1], X.shape[2]))
        
        if use_time_series_cv:
            # Time Series Cross-Validation
            return self._train_with_cv(X, y, epochs, batch_size, patience, n_splits)
        
        # Standard train/validation split (temporal)
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        logger.info(f"📊 Training samples: {len(X_train)}, Validation samples: {len(X_val)}")
        
        # Train with callbacks
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=self._get_callbacks(patience),
            verbose=1
        )
        
        # Calculate training time
        training_time = (datetime.now() - start_time).total_seconds()
        
        # Evaluate on validation set
        val_predictions = self.model.predict(X_val, verbose=0).flatten()
        
        # Inverse transform predictions for real metrics
        val_predictions_real = self.target_scaler.inverse_transform(val_predictions.reshape(-1, 1)).flatten()
        y_val_real = self.target_scaler.inverse_transform(y_val.reshape(-1, 1)).flatten()
        
        # Calculate metrics
        metrics = self._calculate_metrics(y_val_real, val_predictions_real)
        
        self.training_history = history.history
        self.evaluation_metrics = metrics
        self.is_fitted = True
        
        # Save model and scalers
        self.save_model()
        
        result = {
            'epochs_trained': len(history.history['loss']),
            'training_time_seconds': round(training_time, 2),
            'final_train_loss': round(history.history['loss'][-1], 6),
            'final_val_loss': round(history.history['val_loss'][-1], 6),
            'best_val_loss': round(min(history.history['val_loss']), 6),
            'metrics': metrics,
            'early_stopped': len(history.history['loss']) < epochs
        }
        
        logger.info(f"✅ Training completed in {training_time:.1f}s")
        logger.info(f"📊 Best validation loss: {result['best_val_loss']:.6f}")
        logger.info(f"📊 RMSE: {metrics['rmse']:.2f}, MAE: {metrics['mae']:.2f}, MAPE: {metrics['mape']:.2f}%")
        
        return result
    
    def _train_with_cv(self, X: np.ndarray, y: np.ndarray,
                       epochs: int, batch_size: int, 
                       patience: int, n_splits: int) -> Dict[str, Any]:
        """Train with Time Series Cross-Validation
        
        Args:
            X: Feature sequences
            y: Target values
            epochs: Maximum epochs
            batch_size: Batch size
            patience: Early stopping patience
            n_splits: Number of CV splits
            
        Returns:
            Dict with CV results
        """
        logger.info(f"🔄 Training with {n_splits}-fold Time Series CV...")
        
        tscv = TimeSeriesSplit(n_splits=n_splits)
        fold_results = []
        
        for fold, (train_idx, val_idx) in enumerate(tscv.split(X), 1):
            logger.info(f"📁 Fold {fold}/{n_splits}")
            
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            
            # Reset model for each fold
            self.model = self.build_model((X.shape[1], X.shape[2]))
            
            history = self.model.fit(
                X_train, y_train,
                validation_data=(X_val, y_val),
                epochs=epochs,
                batch_size=batch_size,
                callbacks=self._get_callbacks(patience),
                verbose=0
            )
            
            # Evaluate fold
            val_predictions = self.model.predict(X_val, verbose=0).flatten()
            val_predictions_real = self.target_scaler.inverse_transform(val_predictions.reshape(-1, 1)).flatten()
            y_val_real = self.target_scaler.inverse_transform(y_val.reshape(-1, 1)).flatten()
            
            metrics = self._calculate_metrics(y_val_real, val_predictions_real)
            metrics['fold'] = fold
            metrics['epochs_trained'] = len(history.history['loss'])
            fold_results.append(metrics)
        
        # Aggregate results
        avg_rmse = np.mean([r['rmse'] for r in fold_results])
        avg_mae = np.mean([r['mae'] for r in fold_results])
        avg_mape = np.mean([r['mape'] for r in fold_results])
        
        self.is_fitted = True
        self.save_model()
        
        result = {
            'cv_folds': n_splits,
            'fold_results': fold_results,
            'avg_rmse': round(avg_rmse, 4),
            'avg_mae': round(avg_mae, 4),
            'avg_mape': round(avg_mape, 4),
            'std_rmse': round(np.std([r['rmse'] for r in fold_results]), 4)
        }
        
        logger.info(f"✅ CV completed. Avg RMSE: {avg_rmse:.2f} ± {result['std_rmse']:.2f}")
        
        return result
    
    def _calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Calculate evaluation metrics
        
        Args:
            y_true: True values
            y_pred: Predicted values
            
        Returns:
            Dict with RMSE, MAE, MAPE, R²
        """
        # Avoid division by zero for MAPE
        mask = y_true != 0
        
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mae = mean_absolute_error(y_true, y_pred)
        
        if mask.sum() > 0:
            mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
        else:
            mape = 0.0
        
        # R² score
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        
        return {
            'rmse': round(rmse, 4),
            'mae': round(mae, 4),
            'mape': round(mape, 4),
            'r2': round(r2, 4)
        }
    
    def predict(self, recent_data: pd.DataFrame, hours_ahead: int = 24) -> List[float]:
        """Predict demand for the next hours
        
        Args:
            recent_data: DataFrame with recent features (at least sequence_length rows)
            hours_ahead: Number of hours to predict
            
        Returns:
            List of predicted demand values
        """
        # Try to use TensorFlow model
        if HAS_TENSORFLOW and self.model is None:
            self.load_model()
        
        if not HAS_TENSORFLOW or self.model is None:
            logger.info("📊 Using rule-based prediction (TensorFlow not available)")
            return self._rule_based_predict(recent_data, hours_ahead)
        
        try:
            # Validate data
            if len(recent_data) < self.sequence_length:
                logger.warning(f"⚠️ Need at least {self.sequence_length} rows, got {len(recent_data)}")
                return self._rule_based_predict(recent_data, hours_ahead)
            
            # Get last sequence
            last_data = recent_data[self.FEATURES].tail(self.sequence_length)
            last_sequence = self.scaler.transform(last_data)
            last_sequence = last_sequence.reshape(1, self.sequence_length, -1)
            
            # Generate predictions autoregressively
            predictions = []
            current_sequence = last_sequence.copy()
            
            for _ in range(hours_ahead):
                pred_scaled = self.model.predict(current_sequence, verbose=0)[0, 0]
                
                # Inverse transform prediction
                pred_real = self.target_scaler.inverse_transform([[pred_scaled]])[0, 0]
                predictions.append(max(0, float(pred_real)))
                
                # Update sequence for next prediction
                current_sequence = np.roll(current_sequence, -1, axis=1)
                # Update demand-related features in the last position
                current_sequence[0, -1, -2] = pred_scaled  # previous_demand
                current_sequence[0, -1, -1] = np.mean(current_sequence[0, -6:, -1])  # rolling_mean
            
            logger.info(f"✅ Generated {hours_ahead} LSTM predictions")
            return predictions
            
        except Exception as e:
            logger.error(f"❌ Error in TensorFlow prediction: {e}")
            return self._rule_based_predict(recent_data, hours_ahead)
    
    def _rule_based_predict(self, recent_data: pd.DataFrame, hours_ahead: int = 24) -> List[float]:
        """Realistic rule-based prediction with peak hours
        
        Args:
            recent_data: DataFrame with recent data (used to get starting hour)
            hours_ahead: Number of hours to predict
            
        Returns:
            List of predicted demand values
        """
        # Get current hour
        if recent_data is not None and not recent_data.empty and 'hour' in recent_data.columns:
            start_hour = int(recent_data.iloc[-1]['hour'])
        else:
            start_hour = datetime.now().hour
        
        predictions = []
        for i in range(hours_ahead):
            hour = (start_hour + i + 1) % 24
            
            # Realistic demand patterns based on typical transit usage
            if hour in [7, 8]:  # Morning peak (7am-9am)
                base_demand = 180 + np.random.uniform(-15, 20)
            elif hour in [17, 18, 19]:  # Evening peak (5pm-8pm)
                base_demand = 195 + np.random.uniform(-18, 25)
            elif hour in [9, 10, 11, 12]:  # Late morning
                base_demand = 95 + np.random.uniform(-10, 15)
            elif hour in [13, 14, 15, 16]:  # Afternoon
                base_demand = 105 + np.random.uniform(-12, 18)
            elif hour in [20, 21, 22]:  # Evening
                base_demand = 65 + np.random.uniform(-8, 12)
            elif hour in [23, 0, 1, 2, 3, 4, 5]:  # Night
                base_demand = 25 + np.random.uniform(-5, 8)
            else:  # Early morning (6am)
                base_demand = 55 + np.random.uniform(-8, 12)
            
            predictions.append(max(10, float(base_demand)))
        
        return predictions
    
    def evaluate(self, test_data: pd.DataFrame) -> Dict[str, Any]:
        """Evaluate model on test data
        
        Args:
            test_data: DataFrame with test features and demand
            
        Returns:
            Dict with evaluation metrics
        """
        if not self.is_fitted:
            return {'error': 'Model not fitted'}
        
        X_test, y_test = self.prepare_data(test_data, fit_scaler=False)
        
        if HAS_TENSORFLOW and self.model is not None:
            predictions = self.model.predict(X_test, verbose=0).flatten()
            predictions_real = self.target_scaler.inverse_transform(predictions.reshape(-1, 1)).flatten()
        else:
            # Use rule-based predictions
            predictions_real = np.array(self._rule_based_predict(test_data, len(y_test)))
        
        y_test_real = self.target_scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()
        
        metrics = self._calculate_metrics(y_test_real, predictions_real)
        
        return {
            'test_samples': len(y_test),
            'metrics': metrics,
            'predictions_sample': predictions_real[:10].tolist(),
            'actuals_sample': y_test_real[:10].tolist()
        }
    
    def save_model(self, path: Optional[str] = None) -> Dict[str, str]:
        """Save model, scalers, and metadata
        
        Args:
            path: Custom path for model (optional)
            
        Returns:
            Dict with saved file paths
        """
        model_path = path or self.model_path
        scaler_path = self.scaler_path
        metadata_path = self.metadata_path
        
        # Ensure directories exist
        for p in [model_path, scaler_path, metadata_path]:
            dir_path = os.path.dirname(p)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
        
        saved_files = {}
        
        # Save Keras model
        if HAS_TENSORFLOW and self.model is not None:
            self.model.save(model_path)
            saved_files['model'] = model_path
            logger.info(f"✅ Model saved to {model_path}")
        
        # Save scalers
        scalers = {
            'feature_scaler': self.scaler,
            'target_scaler': self.target_scaler
        }
        joblib.dump(scalers, scaler_path)
        saved_files['scalers'] = scaler_path
        
        # Save metadata
        metadata = {
            'sequence_length': self.sequence_length,
            'features': self.FEATURES,
            'is_fitted': self.is_fitted,
            'evaluation_metrics': self.evaluation_metrics,
            'saved_at': datetime.now().isoformat(),
            'tensorflow_version': tf.__version__ if HAS_TENSORFLOW and tf else None
        }
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        saved_files['metadata'] = metadata_path
        
        logger.info(f"✅ All model artifacts saved")
        return saved_files
    
    def load_model(self, path: Optional[str] = None) -> bool:
        """Load model, scalers, and metadata
        
        Args:
            path: Custom path for model (optional)
            
        Returns:
            True if loaded successfully
        """
        model_path = path or self.model_path
        
        try:
            # Load Keras model
            if HAS_TENSORFLOW and os.path.exists(model_path):
                try:
                    # Intentar cargar normalmente
                    self.model = load_model(model_path)
                except Exception as e1:
                    try:
                        # Si falla, intentar sin compilar (evita problemas con métricas)
                        self.model = load_model(model_path, compile=False)
                        # Recompilar manualmente
                        self.model.compile(
                            optimizer=Adam(learning_rate=0.001),
                            loss='mse',
                            metrics=['mae']
                        )
                        logger.info(f"✅ Model loaded and recompiled from {model_path}")
                    except Exception as e2:
                        logger.warning(f"⚠️ Could not load model: {e2}")
                        return False
                else:
                    logger.info(f"✅ Model loaded from {model_path}")
            
            # Load scalers
            if os.path.exists(self.scaler_path):
                scalers = joblib.load(self.scaler_path)
                self.scaler = scalers['feature_scaler']
                self.target_scaler = scalers['target_scaler']
                logger.info(f"✅ Scalers loaded from {self.scaler_path}")
            
            # Load metadata
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'r') as f:
                    metadata = json.load(f)
                self.sequence_length = metadata.get('sequence_length', 24)
                self.is_fitted = metadata.get('is_fitted', True)
                self.evaluation_metrics = metadata.get('evaluation_metrics')
            
            self.is_fitted = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model
        
        Returns:
            Dict with model configuration and state
        """
        info = {
            'is_fitted': self.is_fitted,
            'has_tensorflow': HAS_TENSORFLOW,
            'tensorflow_version': tf.__version__ if HAS_TENSORFLOW and tf else None,
            'sequence_length': self.sequence_length,
            'features': self.FEATURES,
            'model_path': self.model_path,
            'model_exists': os.path.exists(self.model_path),
            'evaluation_metrics': self.evaluation_metrics
        }
        
        if HAS_TENSORFLOW and self.model is not None:
            info['model_summary'] = {
                'total_params': self.model.count_params(),
                'layers': len(self.model.layers),
                'optimizer': self.model.optimizer.__class__.__name__,
                'loss': self.model.loss
            }
        
        return info
    
    def generate_synthetic_data(self, num_samples: int = 1000) -> pd.DataFrame:
        """Generate synthetic training data with realistic patterns
        
        Args:
            num_samples: Number of hourly samples to generate
            
        Returns:
            DataFrame with features and demand
        """
        logger.info(f"📊 Generating {num_samples} synthetic samples...")
        
        dates = pd.date_range(start='2024-01-01', periods=num_samples, freq='H')
        
        data = pd.DataFrame({
            'timestamp': dates,
            'hour': dates.hour,
            'day_of_week': dates.dayofweek,
            'month': dates.month,
            'is_weekend': (dates.dayofweek >= 5).astype(int),
            'is_holiday': np.random.choice([0, 1], num_samples, p=[0.95, 0.05]),
            'temperature': np.random.normal(20, 5, num_samples),
            'precipitation': np.random.exponential(2, num_samples),
            'events_count': np.random.poisson(0.5, num_samples),
        })
        
        # Generate realistic demand with peak hours
        demand = np.zeros(num_samples)
        
        for i in range(num_samples):
            hour = data.iloc[i]['hour']
            is_weekend = data.iloc[i]['is_weekend']
            is_holiday = data.iloc[i]['is_holiday']
            
            # Base demand by hour (realistic transit pattern)
            if hour in [7, 8]:
                base = 180
            elif hour in [17, 18, 19]:
                base = 195
            elif hour in [9, 10, 11, 12]:
                base = 95
            elif hour in [13, 14, 15, 16]:
                base = 105
            elif hour in [20, 21, 22]:
                base = 65
            elif hour in [23, 0, 1, 2, 3, 4, 5]:
                base = 25
            else:
                base = 55
            
            # Weekend effect (lower demand)
            if is_weekend:
                base *= 0.7
            
            # Holiday effect
            if is_holiday:
                base *= 0.5
            
            # Add noise
            demand[i] = max(5, base + np.random.normal(0, 10))
        
        data['demand'] = demand
        data['previous_demand'] = data['demand'].shift(1).ffill()
        data['rolling_mean'] = data['demand'].rolling(window=6, min_periods=1).mean()
        
        logger.info("✅ Synthetic data generated")
        return data


# Global instance
lstm_predictor = LSTMDemandPredictor()
