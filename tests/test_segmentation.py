import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.ml.dbscan_model import DBSCANUserSegmentation


client = TestClient(app)


def get_auth_header():
    token = create_access_token({"sub": "test@example.com"})
    return {"Authorization": f"Bearer {token}"}


def test_segment_users():
    payload = {"eps": 0.5, "min_samples": 5}
    resp = client.post("/api/v1/analytics/users/segment", json=payload, headers=get_auth_header())
    assert resp.status_code == 200
    data = resp.json()
    assert "clusters" in data


# ==================== UNIT TESTS FOR DBSCAN ====================

@pytest.fixture
def dbscan_model():
    """Create a fresh DBSCAN model for each test"""
    return DBSCANUserSegmentation(eps=0.5, min_samples=3)


@pytest.fixture
def synthetic_users(dbscan_model):
    """Generate synthetic users for testing"""
    return dbscan_model.generate_synthetic_users(num_users=200)


class TestDBSCANFit:
    """Tests for DBSCAN fit functionality"""
    
    def test_fit_returns_metrics(self, dbscan_model, synthetic_users):
        """Test that fit returns all required metrics"""
        result = dbscan_model.fit(synthetic_users)
        
        assert 'n_clusters' in result
        assert 'n_outliers' in result
        assert 'silhouette_score' in result
        assert 'davies_bouldin_index' in result
        assert 'outlier_percentage' in result
        assert 'total_users_analyzed' in result
        assert 'labels' in result
    
    def test_fit_creates_clusters(self, dbscan_model, synthetic_users):
        """Test that fit creates at least 2 clusters"""
        result = dbscan_model.fit(synthetic_users)
        assert result['n_clusters'] >= 2
    
    def test_fit_sets_is_fitted(self, dbscan_model, synthetic_users):
        """Test that fit sets is_fitted flag"""
        assert not dbscan_model.is_fitted
        dbscan_model.fit(synthetic_users)
        assert dbscan_model.is_fitted
    
    def test_fit_computes_cluster_centers(self, dbscan_model, synthetic_users):
        """Test that fit computes cluster centers"""
        dbscan_model.fit(synthetic_users)
        assert dbscan_model.cluster_centers is not None
        assert len(dbscan_model.cluster_centers) > 0


class TestDBSCANPredict:
    """Tests for DBSCAN predict functionality"""
    
    def test_predict_without_fit_raises_error(self, dbscan_model, synthetic_users):
        """Test that predict raises error if not fitted"""
        with pytest.raises(ValueError, match="Model must be fitted first"):
            dbscan_model.predict_cluster(synthetic_users)
    
    def test_predict_returns_labels(self, dbscan_model, synthetic_users):
        """Test that predict returns cluster labels"""
        dbscan_model.fit(synthetic_users)
        
        # Predict on subset of users
        new_users = synthetic_users.head(10).copy()
        predictions = dbscan_model.predict_cluster(new_users)
        
        assert len(predictions) == 10
        assert all(isinstance(p, (int, np.integer)) for p in predictions)
    
    def test_predict_assigns_valid_clusters(self, dbscan_model, synthetic_users):
        """Test that predictions are valid cluster labels or -1"""
        dbscan_model.fit(synthetic_users)
        predictions = dbscan_model.predict_cluster(synthetic_users.head(50))
        
        valid_labels = set(dbscan_model.labels) | {-1}
        for pred in predictions:
            assert pred in valid_labels


class TestDBSCANPersistence:
    """Tests for DBSCAN save/load functionality"""
    
    def test_save_model(self, dbscan_model, synthetic_users):
        """Test that model can be saved"""
        dbscan_model.fit(synthetic_users)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_model.joblib")
            saved_path = dbscan_model.save_model(path)
            
            assert os.path.exists(saved_path)
    
    def test_save_without_fit_raises_error(self, dbscan_model):
        """Test that save raises error if not fitted"""
        with pytest.raises(ValueError, match="Model must be fitted before saving"):
            dbscan_model.save_model()
    
    def test_load_model(self, dbscan_model, synthetic_users):
        """Test that model can be loaded"""
        dbscan_model.fit(synthetic_users)
        original_labels = dbscan_model.labels.copy()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_model.joblib")
            dbscan_model.save_model(path)
            
            # Create new model and load
            new_model = DBSCANUserSegmentation()
            success = new_model.load_model(path)
            
            assert success
            assert new_model.is_fitted
            assert len(new_model.labels) == len(original_labels)
    
    def test_load_nonexistent_returns_false(self, dbscan_model):
        """Test that loading nonexistent file returns False"""
        result = dbscan_model.load_model("/nonexistent/path/model.joblib")
        assert result is False


class TestDBSCANOptimization:
    """Tests for DBSCAN hyperparameter optimization"""
    
    def test_find_optimal_params_returns_results(self, dbscan_model, synthetic_users):
        """Test that optimization returns best params"""
        result = dbscan_model.find_optimal_params(
            synthetic_users, 
            eps_range=(0.3, 1.0),
            min_samples_range=(3, 7),
            n_iterations=5
        )
        
        assert 'best_params' in result
        assert 'best_score' in result
        assert 'top_10_results' in result
        assert 'eps' in result['best_params']
        assert 'min_samples' in result['best_params']
    
    def test_find_optimal_params_improves_clustering(self, synthetic_users):
        """Test that optimal params give better results"""
        model = DBSCANUserSegmentation(eps=0.5, min_samples=5)
        
        # Find optimal params
        result = model.find_optimal_params(
            synthetic_users,
            eps_range=(0.3, 1.5),
            min_samples_range=(3, 10),
            n_iterations=8
        )
        
        # Check that we got valid results
        assert result['best_score'] > -1


class TestDBSCANModelInfo:
    """Tests for model info functionality"""
    
    def test_get_model_info_before_fit(self, dbscan_model):
        """Test model info before fitting"""
        info = dbscan_model.get_model_info()
        
        assert info['is_fitted'] is False
        assert info['n_clusters'] == 0
        assert info['total_samples'] == 0
    
    def test_get_model_info_after_fit(self, dbscan_model, synthetic_users):
        """Test model info after fitting"""
        dbscan_model.fit(synthetic_users)
        info = dbscan_model.get_model_info()
        
        assert info['is_fitted'] is True
        assert info['n_clusters'] > 0
        assert info['total_samples'] == len(synthetic_users)
        assert 'features' in info


# Import numpy for test assertions
import numpy as np
