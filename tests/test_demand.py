import pytest
import tempfile
import os
import numpy as np
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.ml.lstm_model import LSTMDemandPredictor, HAS_TENSORFLOW


client = TestClient(app)


def get_auth_header():
    token = create_access_token({"sub": "test@example.com"})
    return {"Authorization": f"Bearer {token}"}


def test_predict_demand():
    payload = {"route_id": 1, "hours_ahead": 4}
    resp = client.post("/api/v1/analytics/demand/predict", json=payload, headers=get_auth_header())
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("route_id") == 1
    assert "predictions" in data


# ==================== UNIT TESTS FOR LSTM ====================

@pytest.fixture
def lstm_model():
    """Create a fresh LSTM model for each test"""
    return LSTMDemandPredictor(sequence_length=24)


@pytest.fixture
def synthetic_data(lstm_model):
    """Generate synthetic data for testing"""
    return lstm_model.generate_synthetic_data(num_samples=500)


class TestLSTMDataPreparation:
    """Tests for LSTM data preparation"""
    
    def test_generate_synthetic_data(self, lstm_model):
        """Test that synthetic data generation works"""
        data = lstm_model.generate_synthetic_data(num_samples=100)
        
        assert len(data) == 100
        assert 'demand' in data.columns
        assert 'hour' in data.columns
        assert 'previous_demand' in data.columns
        assert 'rolling_mean' in data.columns
    
    def test_prepare_data_creates_sequences(self, lstm_model, synthetic_data):
        """Test that prepare_data creates correct sequences"""
        X, y = lstm_model.prepare_data(synthetic_data)
        
        expected_samples = len(synthetic_data) - lstm_model.sequence_length
        assert len(X) == expected_samples
        assert len(y) == expected_samples
        assert X.shape[1] == lstm_model.sequence_length
        assert X.shape[2] == len(lstm_model.FEATURES)
    
    def test_prepare_data_missing_features_raises_error(self, lstm_model):
        """Test that missing features raise an error"""
        import pandas as pd
        bad_data = pd.DataFrame({'hour': [1, 2, 3]})
        
        with pytest.raises(ValueError, match="Missing features"):
            lstm_model.prepare_data(bad_data)
    
    def test_prepare_data_missing_demand_raises_error(self, lstm_model, synthetic_data):
        """Test that missing demand column raises an error"""
        data_no_demand = synthetic_data.drop(columns=['demand'])
        
        with pytest.raises(ValueError, match="Missing 'demand' column"):
            lstm_model.prepare_data(data_no_demand)


class TestLSTMPrediction:
    """Tests for LSTM prediction"""
    
    def test_rule_based_predict_returns_correct_length(self, lstm_model, synthetic_data):
        """Test that rule-based prediction returns correct number of predictions"""
        predictions = lstm_model._rule_based_predict(synthetic_data, hours_ahead=12)
        
        assert len(predictions) == 12
    
    def test_rule_based_predict_all_positive(self, lstm_model, synthetic_data):
        """Test that all predictions are positive"""
        predictions = lstm_model._rule_based_predict(synthetic_data, hours_ahead=24)
        
        assert all(p > 0 for p in predictions)
    
    def test_predict_without_model_uses_fallback(self, lstm_model, synthetic_data):
        """Test that predict uses fallback when no model"""
        predictions = lstm_model.predict(synthetic_data, hours_ahead=6)
        
        assert len(predictions) == 6
        assert all(isinstance(p, float) for p in predictions)
    
    def test_predict_peak_hours_higher_demand(self, lstm_model):
        """Test that peak hours have higher demand predictions"""
        import pandas as pd
        
        # Morning data (hour 7)
        morning_data = pd.DataFrame({'hour': [7]})
        morning_pred = lstm_model._rule_based_predict(morning_data, hours_ahead=1)[0]
        
        # Night data (hour 2)
        night_data = pd.DataFrame({'hour': [2]})
        night_pred = lstm_model._rule_based_predict(night_data, hours_ahead=1)[0]
        
        # Morning peak should be higher than night
        assert morning_pred > night_pred


class TestLSTMMetrics:
    """Tests for LSTM metrics calculation"""
    
    def test_calculate_metrics_returns_all_metrics(self, lstm_model):
        """Test that all metrics are calculated"""
        y_true = np.array([100, 150, 200, 175, 125])
        y_pred = np.array([95, 155, 195, 180, 120])
        
        metrics = lstm_model._calculate_metrics(y_true, y_pred)
        
        assert 'rmse' in metrics
        assert 'mae' in metrics
        assert 'mape' in metrics
        assert 'r2' in metrics
    
    def test_calculate_metrics_perfect_prediction(self, lstm_model):
        """Test metrics with perfect predictions"""
        y_true = np.array([100, 150, 200])
        y_pred = np.array([100, 150, 200])
        
        metrics = lstm_model._calculate_metrics(y_true, y_pred)
        
        assert metrics['rmse'] == 0
        assert metrics['mae'] == 0
        assert metrics['r2'] == 1.0


class TestLSTMPersistence:
    """Tests for LSTM save/load functionality"""
    
    def test_save_model_creates_files(self, lstm_model, synthetic_data):
        """Test that save creates necessary files"""
        lstm_model.is_fitted = True
        
        with tempfile.TemporaryDirectory() as tmpdir:
            lstm_model.model_path = os.path.join(tmpdir, "model.h5")
            lstm_model.scaler_path = os.path.join(tmpdir, "scaler.joblib")
            lstm_model.metadata_path = os.path.join(tmpdir, "metadata.json")
            
            # Fit the scaler first
            lstm_model.prepare_data(synthetic_data, fit_scaler=True)
            
            saved_files = lstm_model.save_model()
            
            assert os.path.exists(lstm_model.scaler_path)
            assert os.path.exists(lstm_model.metadata_path)
    
    def test_load_model_restores_state(self, lstm_model, synthetic_data):
        """Test that load restores model state"""
        lstm_model.is_fitted = True
        
        with tempfile.TemporaryDirectory() as tmpdir:
            lstm_model.model_path = os.path.join(tmpdir, "model.h5")
            lstm_model.scaler_path = os.path.join(tmpdir, "scaler.joblib")
            lstm_model.metadata_path = os.path.join(tmpdir, "metadata.json")
            
            # Fit and save
            lstm_model.prepare_data(synthetic_data, fit_scaler=True)
            lstm_model.save_model()
            
            # Create new model and load
            new_model = LSTMDemandPredictor()
            new_model.model_path = lstm_model.model_path
            new_model.scaler_path = lstm_model.scaler_path
            new_model.metadata_path = lstm_model.metadata_path
            
            success = new_model.load_model()
            
            assert success
            assert new_model.is_fitted


class TestLSTMModelInfo:
    """Tests for model info functionality"""
    
    def test_get_model_info_before_fit(self, lstm_model):
        """Test model info before fitting"""
        info = lstm_model.get_model_info()
        
        assert info['is_fitted'] is False
        assert 'features' in info
        assert info['sequence_length'] == 24
    
    def test_get_model_info_has_tensorflow_flag(self, lstm_model):
        """Test that model info includes TensorFlow status"""
        info = lstm_model.get_model_info()
        
        assert 'has_tensorflow' in info
        assert isinstance(info['has_tensorflow'], bool)


@pytest.mark.skipif(not HAS_TENSORFLOW, reason="TensorFlow not available")
class TestLSTMTraining:
    """Tests for LSTM training (requires TensorFlow)"""
    
    def test_build_model_creates_model(self, lstm_model):
        """Test that build_model creates a Keras model"""
        model = lstm_model.build_model((24, 10))
        
        assert model is not None
        assert len(model.layers) > 0
    
    def test_train_returns_metrics(self, lstm_model, synthetic_data):
        """Test that training returns metrics"""
        result = lstm_model.train(
            synthetic_data,
            epochs=2,
            batch_size=32,
            patience=1
        )
        
        assert 'epochs_trained' in result
        assert 'metrics' in result
        assert lstm_model.is_fitted
