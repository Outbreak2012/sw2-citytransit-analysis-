import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.neighbors import NearestNeighbors
import logging
import os
import joblib
from typing import List, Dict, Any, Optional, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)


class DBSCANUserSegmentation:
    """DBSCAN for user segmentation with full ML pipeline support"""
    
    # Features utilizadas para clustering
    FEATURES = [
        'usage_frequency',
        'avg_spending',
        'route_diversity',
        'peak_hour_usage_ratio',
        'weekend_usage_ratio',
        'avg_trip_duration',
        'total_transactions'
    ]
    
    def __init__(self, eps: float = 0.5, min_samples: int = 5):
        self.eps = eps
        self.min_samples = min_samples
        self.scaler = StandardScaler()
        self.model = None
        self.labels = None
        self.fitted_data = None  # Store fitted data for prediction
        self.cluster_centers = None  # Store cluster centers
        self.model_path = getattr(settings, 'DBSCAN_MODEL_PATH', 'models/dbscan_model.joblib')
        self.is_fitted = False
        
    def prepare_user_features(self, users_data: pd.DataFrame, fit_scaler: bool = True):
        """Prepare user features for clustering
        
        Args:
            users_data: DataFrame with user data
            fit_scaler: If True, fit the scaler. If False, only transform (for prediction)
        
        Returns:
            Tuple of (scaled_features, feature_names)
        """
        # Handle missing values
        users_data = users_data.fillna(0)
        
        # Validate all features exist
        missing_features = [f for f in self.FEATURES if f not in users_data.columns]
        if missing_features:
            raise ValueError(f"Missing features: {missing_features}")
        
        # Scale features
        if fit_scaler:
            scaled_features = self.scaler.fit_transform(users_data[self.FEATURES])
        else:
            scaled_features = self.scaler.transform(users_data[self.FEATURES])
        
        return scaled_features, self.FEATURES
    
    def fit(self, users_data: pd.DataFrame) -> Dict[str, Any]:
        """Fit DBSCAN model
        
        Args:
            users_data: DataFrame with user features
            
        Returns:
            Dict with clustering metrics
        """
        logger.info("🤖 Fitting DBSCAN clustering model...")
        
        X, feature_names = self.prepare_user_features(users_data, fit_scaler=True)
        self.fitted_data = X  # Store for prediction
        
        # Fit DBSCAN
        self.model = DBSCAN(eps=self.eps, min_samples=self.min_samples, n_jobs=-1)
        self.labels = self.model.fit_predict(X)
        
        # Calculate metrics
        n_clusters = len(set(self.labels)) - (1 if -1 in self.labels else 0)
        n_outliers = list(self.labels).count(-1)
        
        # Calculate cluster centers for prediction
        self._compute_cluster_centers(X)
        
        # Calculate silhouette score (excluding outliers)
        mask = self.labels != -1
        silhouette_avg = None
        davies_bouldin = None
        
        if n_clusters > 1 and mask.sum() > 0:
            silhouette_avg = silhouette_score(X[mask], self.labels[mask])
            davies_bouldin = davies_bouldin_score(X[mask], self.labels[mask])
        
        self.is_fitted = True
        
        logger.info(f"✅ DBSCAN completed: {n_clusters} clusters, {n_outliers} outliers")
        if silhouette_avg:
            logger.info(f"📊 Silhouette score: {silhouette_avg:.3f}")
        if davies_bouldin:
            logger.info(f"📊 Davies-Bouldin index: {davies_bouldin:.3f}")
        
        return {
            'n_clusters': n_clusters,
            'n_outliers': n_outliers,
            'outlier_percentage': round(n_outliers / len(self.labels) * 100, 2),
            'silhouette_score': round(silhouette_avg, 4) if silhouette_avg else None,
            'davies_bouldin_index': round(davies_bouldin, 4) if davies_bouldin else None,
            'total_users_analyzed': len(self.labels),
            'labels': self.labels
        }
    
    def _compute_cluster_centers(self, X: np.ndarray):
        """Compute cluster centers for prediction"""
        unique_labels = set(self.labels)
        if -1 in unique_labels:
            unique_labels.remove(-1)
        
        self.cluster_centers = {}
        for label in unique_labels:
            mask = self.labels == label
            self.cluster_centers[label] = X[mask].mean(axis=0)
    
    def analyze_clusters(self, users_data: pd.DataFrame):
        """Analyze cluster characteristics"""
        if self.labels is None:
            raise ValueError("Model must be fitted first")
        
        users_data['cluster'] = self.labels
        clusters = []
        
        # Analyze each cluster
        unique_clusters = set(self.labels)
        if -1 in unique_clusters:
            unique_clusters.remove(-1)  # Exclude outliers from analysis
        
        for cluster_id in unique_clusters:
            cluster_data = users_data[users_data['cluster'] == cluster_id]
            
            cluster_info = {
                'cluster_id': int(cluster_id),
                'user_count': len(cluster_data),
                'avg_frequency': float(cluster_data['usage_frequency'].mean()),
                'avg_spending': float(cluster_data['avg_spending'].mean()),
                'avg_route_diversity': float(cluster_data['route_diversity'].mean()),
                'peak_hour_ratio': float(cluster_data['peak_hour_usage_ratio'].mean()),
                'weekend_ratio': float(cluster_data['weekend_usage_ratio'].mean()),
                'characteristics': self._describe_cluster(cluster_data)
            }
            
            clusters.append(cluster_info)
        
        # Outliers analysis
        outliers = users_data[users_data['cluster'] == -1]
        outliers_info = {
            'count': len(outliers),
            'avg_frequency': float(outliers['usage_frequency'].mean()) if len(outliers) > 0 else 0,
            'avg_spending': float(outliers['avg_spending'].mean()) if len(outliers) > 0 else 0
        }
        
        logger.info(f"✅ Analyzed {len(clusters)} clusters")
        return clusters, outliers_info
    
    def _describe_cluster(self, cluster_data: pd.DataFrame) -> str:
        """Generate cluster description"""
        freq = cluster_data['usage_frequency'].mean()
        spending = cluster_data['avg_spending'].mean()
        
        # Classify cluster
        if freq > cluster_data['usage_frequency'].quantile(0.75):
            freq_label = "Alta frecuencia"
        elif freq > cluster_data['usage_frequency'].quantile(0.5):
            freq_label = "Frecuencia media"
        else:
            freq_label = "Baja frecuencia"
        
        if spending > cluster_data['avg_spending'].quantile(0.75):
            spending_label = "Alto gasto"
        elif spending > cluster_data['avg_spending'].quantile(0.5):
            spending_label = "Gasto medio"
        else:
            spending_label = "Bajo gasto"
        
        return f"{freq_label} - {spending_label}"
    
    def generate_synthetic_users(self, num_users: int = 500):
        """Generate synthetic user data for testing"""
        logger.info(f"📊 Generating {num_users} synthetic users...")
        
        # Create different user profiles
        profiles = []
        
        # Profile 1: Frequent commuters (40%)
        n_commuters = int(num_users * 0.4)
        profiles.append(pd.DataFrame({
            'user_id': range(1, n_commuters + 1),
            'usage_frequency': np.random.normal(20, 3, n_commuters).clip(15, 30),
            'avg_spending': np.random.normal(150, 20, n_commuters).clip(100, 200),
            'route_diversity': np.random.normal(2, 0.5, n_commuters).clip(1, 3),
            'peak_hour_usage_ratio': np.random.normal(0.7, 0.1, n_commuters).clip(0.5, 0.9),
            'weekend_usage_ratio': np.random.normal(0.2, 0.1, n_commuters).clip(0, 0.4),
            'avg_trip_duration': np.random.normal(30, 5, n_commuters).clip(20, 45),
            'total_transactions': np.random.normal(200, 30, n_commuters).clip(150, 300)
        }))
        
        # Profile 2: Occasional users (30%)
        n_occasional = int(num_users * 0.3)
        start_id = n_commuters + 1
        profiles.append(pd.DataFrame({
            'user_id': range(start_id, start_id + n_occasional),
            'usage_frequency': np.random.normal(8, 2, n_occasional).clip(5, 12),
            'avg_spending': np.random.normal(60, 15, n_occasional).clip(30, 100),
            'route_diversity': np.random.normal(3, 1, n_occasional).clip(2, 5),
            'peak_hour_usage_ratio': np.random.normal(0.5, 0.15, n_occasional).clip(0.2, 0.7),
            'weekend_usage_ratio': np.random.normal(0.5, 0.15, n_occasional).clip(0.3, 0.7),
            'avg_trip_duration': np.random.normal(25, 8, n_occasional).clip(15, 40),
            'total_transactions': np.random.normal(80, 20, n_occasional).clip(50, 120)
        }))
        
        # Profile 3: Weekend warriors (20%)
        n_weekend = int(num_users * 0.2)
        start_id = n_commuters + n_occasional + 1
        profiles.append(pd.DataFrame({
            'user_id': range(start_id, start_id + n_weekend),
            'usage_frequency': np.random.normal(6, 1.5, n_weekend).clip(4, 9),
            'avg_spending': np.random.normal(90, 20, n_weekend).clip(50, 130),
            'route_diversity': np.random.normal(4, 1, n_weekend).clip(3, 6),
            'peak_hour_usage_ratio': np.random.normal(0.3, 0.1, n_weekend).clip(0.1, 0.5),
            'weekend_usage_ratio': np.random.normal(0.8, 0.1, n_weekend).clip(0.6, 1.0),
            'avg_trip_duration': np.random.normal(35, 10, n_weekend).clip(20, 60),
            'total_transactions': np.random.normal(60, 15, n_weekend).clip(40, 90)
        }))
        
        # Profile 4: Outliers (10%)
        n_outliers = num_users - n_commuters - n_occasional - n_weekend
        start_id = n_commuters + n_occasional + n_weekend + 1
        profiles.append(pd.DataFrame({
            'user_id': range(start_id, start_id + n_outliers),
            'usage_frequency': np.random.uniform(0, 40, n_outliers),
            'avg_spending': np.random.uniform(0, 300, n_outliers),
            'route_diversity': np.random.uniform(1, 10, n_outliers),
            'peak_hour_usage_ratio': np.random.uniform(0, 1, n_outliers),
            'weekend_usage_ratio': np.random.uniform(0, 1, n_outliers),
            'avg_trip_duration': np.random.uniform(5, 120, n_outliers),
            'total_transactions': np.random.uniform(1, 500, n_outliers)
        }))
        
        users_data = pd.concat(profiles, ignore_index=True)
        logger.info("✅ Synthetic users generated")
        return users_data
    
    # ==================== NUEVAS FUNCIONALIDADES ====================
    
    def predict_cluster(self, new_users: pd.DataFrame) -> np.ndarray:
        """Predict cluster for new users based on nearest cluster center
        
        DBSCAN no tiene predict nativo, así que usamos distancia a centros.
        Los usuarios muy lejos de todos los centros se marcan como outliers (-1).
        
        Args:
            new_users: DataFrame with new user features
            
        Returns:
            Array of cluster labels
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first. Call fit() before predict_cluster()")
        
        if self.cluster_centers is None or len(self.cluster_centers) == 0:
            logger.warning("⚠️ No cluster centers available. Returning all as outliers.")
            return np.full(len(new_users), -1)
        
        # Transform new data using fitted scaler
        X_new, _ = self.prepare_user_features(new_users, fit_scaler=False)
        
        # Find nearest cluster center for each new user
        predictions = []
        for x in X_new:
            min_dist = float('inf')
            best_cluster = -1
            
            for cluster_id, center in self.cluster_centers.items():
                dist = np.linalg.norm(x - center)
                if dist < min_dist:
                    min_dist = dist
                    best_cluster = cluster_id
            
            # If too far from any center, mark as outlier
            # Threshold: 2 * eps (configurable)
            if min_dist > 2 * self.eps:
                predictions.append(-1)
            else:
                predictions.append(best_cluster)
        
        logger.info(f"✅ Predicted clusters for {len(new_users)} new users")
        return np.array(predictions)
    
    def find_optimal_params(self, users_data: pd.DataFrame, 
                           eps_range: Tuple[float, float] = (0.3, 2.0),
                           min_samples_range: Tuple[int, int] = (3, 15),
                           n_iterations: int = 20) -> Dict[str, Any]:
        """Find optimal eps and min_samples using grid search
        
        Args:
            users_data: DataFrame with user features
            eps_range: (min_eps, max_eps) to search
            min_samples_range: (min_samples_min, min_samples_max) to search
            n_iterations: Number of random combinations to try
            
        Returns:
            Dict with best parameters and metrics
        """
        logger.info("🔍 Searching for optimal DBSCAN parameters...")
        
        X, _ = self.prepare_user_features(users_data, fit_scaler=True)
        
        best_score = -1
        best_params = {'eps': self.eps, 'min_samples': self.min_samples}
        results = []
        
        # Generate parameter combinations
        eps_values = np.linspace(eps_range[0], eps_range[1], n_iterations)
        min_samples_values = range(min_samples_range[0], min_samples_range[1] + 1)
        
        for eps in eps_values:
            for min_samples in min_samples_values:
                try:
                    model = DBSCAN(eps=eps, min_samples=min_samples, n_jobs=-1)
                    labels = model.fit_predict(X)
                    
                    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
                    n_outliers = list(labels).count(-1)
                    outlier_pct = n_outliers / len(labels)
                    
                    # Skip if too many outliers or too few clusters
                    if outlier_pct > 0.5 or n_clusters < 2:
                        continue
                    
                    mask = labels != -1
                    if mask.sum() > 0 and n_clusters > 1:
                        silhouette = silhouette_score(X[mask], labels[mask])
                        db_index = davies_bouldin_score(X[mask], labels[mask])
                        
                        # Combined score: high silhouette, low DB index, reasonable outliers
                        combined_score = silhouette - 0.1 * db_index - 0.5 * outlier_pct
                        
                        results.append({
                            'eps': round(eps, 3),
                            'min_samples': min_samples,
                            'n_clusters': n_clusters,
                            'n_outliers': n_outliers,
                            'silhouette': round(silhouette, 4),
                            'davies_bouldin': round(db_index, 4),
                            'combined_score': round(combined_score, 4)
                        })
                        
                        if combined_score > best_score:
                            best_score = combined_score
                            best_params = {'eps': eps, 'min_samples': min_samples}
                            
                except Exception as e:
                    continue
        
        # Sort by combined score
        results = sorted(results, key=lambda x: x['combined_score'], reverse=True)
        
        logger.info(f"✅ Best params found: eps={best_params['eps']:.3f}, min_samples={best_params['min_samples']}")
        
        return {
            'best_params': best_params,
            'best_score': round(best_score, 4),
            'top_10_results': results[:10],
            'total_combinations_tested': len(results)
        }
    
    def save_model(self, path: Optional[str] = None) -> str:
        """Save model, scaler, and cluster centers to disk
        
        Args:
            path: Custom path. If None, uses default from settings.
            
        Returns:
            Path where model was saved
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before saving")
        
        save_path = path or self.model_path
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Save all components
        model_data = {
            'eps': self.eps,
            'min_samples': self.min_samples,
            'scaler': self.scaler,
            'labels': self.labels,
            'cluster_centers': self.cluster_centers,
            'fitted_data': self.fitted_data,
            'features': self.FEATURES,
            'is_fitted': True
        }
        
        joblib.dump(model_data, save_path)
        logger.info(f"✅ Model saved to {save_path}")
        
        return save_path
    
    def load_model(self, path: Optional[str] = None) -> bool:
        """Load model from disk
        
        Args:
            path: Custom path. If None, uses default from settings.
            
        Returns:
            True if loaded successfully, False otherwise
        """
        load_path = path or self.model_path
        
        if not os.path.exists(load_path):
            logger.warning(f"⚠️ Model file not found: {load_path}")
            return False
        
        try:
            model_data = joblib.load(load_path)
            
            self.eps = model_data['eps']
            self.min_samples = model_data['min_samples']
            self.scaler = model_data['scaler']
            self.labels = model_data['labels']
            self.cluster_centers = model_data['cluster_centers']
            self.fitted_data = model_data['fitted_data']
            self.is_fitted = model_data['is_fitted']
            
            logger.info(f"✅ Model loaded from {load_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model state
        
        Returns:
            Dict with model configuration and state
        """
        return {
            'is_fitted': self.is_fitted,
            'eps': self.eps,
            'min_samples': self.min_samples,
            'n_clusters': len(self.cluster_centers) if self.cluster_centers else 0,
            'total_samples': len(self.labels) if self.labels is not None else 0,
            'n_outliers': list(self.labels).count(-1) if self.labels is not None else 0,
            'features': self.FEATURES,
            'model_path': self.model_path
        }


# Global instance
dbscan_segmentation = DBSCANUserSegmentation()
