"""
Script para entrenar modelos ML/DL de producción con datos reales
Genera métricas de precisión documentadas
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pickle
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===========================
# 1. ENTRENAR DBSCAN (Clustering)
# ===========================
def train_dbscan_model():
    """Entrenar DBSCAN con datos reales de ClickHouse"""
    try:
        from app.db.clickhouse import clickhouse_conn
        from sklearn.cluster import DBSCAN
        from sklearn.metrics import silhouette_score, davies_bouldin_score
        
        logger.info("=" * 60)
        logger.info("🎯 ENTRENANDO MODELO DBSCAN")
        logger.info("=" * 60)
        
        clickhouse_conn.connect()
        
        # Query para obtener features de usuarios
        query = """
        SELECT 
            user_id,
            COUNT(*) as frequency,
            AVG(monto) as avg_spending,
            AVG(CASE WHEN hora >= 6 AND hora <= 9 THEN 1 ELSE 0 END) as morning_usage,
            AVG(CASE WHEN hora >= 17 AND hora <= 20 THEN 1 ELSE 0 END) as evening_usage,
            COUNT(DISTINCT ruta_id) as unique_routes,
            AVG(CASE WHEN tipo_dia = 'Fin de semana' THEN 1 ELSE 0 END) as weekend_usage
        FROM transacciones
        WHERE user_id IS NOT NULL
        GROUP BY user_id
        HAVING frequency >= 3
        """
        
        logger.info("📊 Obteniendo datos de usuarios desde ClickHouse...")
        result = clickhouse_conn.execute(query)
        df = pd.DataFrame(result, columns=['user_id', 'frequency', 'avg_spending', 
                                           'morning_usage', 'evening_usage', 
                                           'unique_routes', 'weekend_usage'])
        logger.info(f"✅ {len(df)} usuarios obtenidos")
        
        # Preparar features
        features = ['frequency', 'avg_spending', 'morning_usage', 'evening_usage', 
                   'unique_routes', 'weekend_usage']
        X = df[features].values
        
        # Normalizar
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Entrenar DBSCAN
        logger.info("🤖 Entrenando DBSCAN...")
        dbscan = DBSCAN(eps=0.5, min_samples=5, metric='euclidean')
        clusters = dbscan.fit_predict(X_scaled)
        
        df['cluster'] = clusters
        
        # Calcular métricas
        n_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
        n_outliers = list(clusters).count(-1)
        
        # Silhouette score (solo para puntos no-outliers)
        mask = clusters != -1
        if mask.sum() > 1 and n_clusters > 1:
            silhouette = silhouette_score(X_scaled[mask], clusters[mask])
            davies_bouldin = davies_bouldin_score(X_scaled[mask], clusters[mask])
        else:
            silhouette = 0
            davies_bouldin = 0
        
        logger.info(f"✅ Clusters encontrados: {n_clusters}")
        logger.info(f"✅ Outliers detectados: {n_outliers} ({n_outliers/len(df)*100:.1f}%)")
        logger.info(f"📊 Silhouette Score: {silhouette:.3f} (rango: -1 a 1, mejor cerca de 1)")
        logger.info(f"📊 Davies-Bouldin Index: {davies_bouldin:.3f} (menor es mejor)")
        
        # Guardar modelo
        os.makedirs('models', exist_ok=True)
        model_data = {
            'model': dbscan,
            'scaler': scaler,
            'features': features,
            'clusters_info': {},
            'metrics': {
                'n_clusters': n_clusters,
                'n_outliers': n_outliers,
                'outlier_percentage': n_outliers/len(df)*100,
                'silhouette_score': float(silhouette),
                'davies_bouldin_index': float(davies_bouldin)
            },
            'trained_at': datetime.now().isoformat()
        }
        
        # Analizar cada cluster
        for cluster_id in range(n_clusters):
            cluster_data = df[df['cluster'] == cluster_id]
            model_data['clusters_info'][f'cluster_{cluster_id}'] = {
                'size': len(cluster_data),
                'avg_frequency': float(cluster_data['frequency'].mean()),
                'avg_spending': float(cluster_data['avg_spending'].mean()),
                'morning_users': float(cluster_data['morning_usage'].mean()),
                'evening_users': float(cluster_data['evening_usage'].mean())
            }
        
        with open('models/dbscan_production.pkl', 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info("💾 Modelo DBSCAN guardado en: models/dbscan_production.pkl")
        
        return model_data['metrics']
        
    except Exception as e:
        logger.error(f"❌ Error entrenando DBSCAN: {e}")
        return None


# ===========================
# 2. ENTRENAR MODELO DE DEMANDA (Time Series)
# ===========================
def train_demand_model():
    """Entrenar modelo de predicción de demanda con Prophet"""
    try:
        from app.db.clickhouse import clickhouse_conn
        
        logger.info("=" * 60)
        logger.info("📈 ENTRENANDO MODELO DE PREDICCIÓN DE DEMANDA")
        logger.info("=" * 60)
        
        clickhouse_conn.connect()
        
        # Query para obtener series temporales
        query = """
        SELECT 
            toDate(fecha_hora) as ds,
            toHour(fecha_hora) as hour,
            COUNT(*) as y,
            AVG(monto) as avg_amount
        FROM transacciones
        WHERE ruta_id = 1
        GROUP BY ds, hour
        ORDER BY ds, hour
        """
        
        logger.info("📊 Obteniendo series temporales desde ClickHouse...")
        result = clickhouse_conn.execute(query)
        df = pd.DataFrame(result, columns=['ds', 'hour', 'y', 'avg_amount'])
        df['ds'] = pd.to_datetime(df['ds'])
        logger.info(f"✅ {len(df)} registros obtenidos")
        
        # Crear features temporales
        df['day_of_week'] = df['ds'].dt.dayofweek
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        df['month'] = df['ds'].dt.month
        df['is_peak_hour'] = ((df['hour'] >= 7) & (df['hour'] <= 9) | 
                              (df['hour'] >= 17) & (df['hour'] <= 19)).astype(int)
        
        # Preparar train/test split
        train_size = int(len(df) * 0.8)
        train_df = df[:train_size].copy()
        test_df = df[train_size:].copy()
        
        # Modelo simple pero efectivo: Gradient Boosting
        from sklearn.ensemble import GradientBoostingRegressor
        
        features = ['hour', 'day_of_week', 'is_weekend', 'month', 'is_peak_hour']
        X_train = train_df[features].values
        y_train = train_df['y'].values
        X_test = test_df[features].values
        y_test = test_df['y'].values
        
        logger.info("🤖 Entrenando Gradient Boosting Regressor...")
        model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        model.fit(X_train, y_train)
        
        # Predicciones
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)
        
        # Métricas
        train_mae = mean_absolute_error(y_train, y_pred_train)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)
        
        # Calcular MAPE
        train_mape = np.mean(np.abs((y_train - y_pred_train) / y_train)) * 100
        test_mape = np.mean(np.abs((y_test - y_pred_test) / y_test)) * 100
        
        logger.info("📊 MÉTRICAS DE ENTRENAMIENTO:")
        logger.info(f"  MAE: {train_mae:.2f} pasajeros")
        logger.info(f"  RMSE: {train_rmse:.2f} pasajeros")
        logger.info(f"  R²: {train_r2:.3f}")
        logger.info(f"  MAPE: {train_mape:.2f}%")
        
        logger.info("📊 MÉTRICAS DE PRUEBA (Test Set):")
        logger.info(f"  MAE: {test_mae:.2f} pasajeros")
        logger.info(f"  RMSE: {test_rmse:.2f} pasajeros")
        logger.info(f"  R²: {test_r2:.3f}")
        logger.info(f"  MAPE: {test_mape:.2f}%")
        logger.info(f"  Precisión estimada: {100 - test_mape:.1f}%")
        
        # Guardar modelo
        model_data = {
            'model': model,
            'features': features,
            'metrics': {
                'train_mae': float(train_mae),
                'test_mae': float(test_mae),
                'train_rmse': float(train_rmse),
                'test_rmse': float(test_rmse),
                'train_r2': float(train_r2),
                'test_r2': float(test_r2),
                'train_mape': float(train_mape),
                'test_mape': float(test_mape),
                'accuracy': float(100 - test_mape)
            },
            'trained_at': datetime.now().isoformat(),
            'training_samples': len(train_df),
            'test_samples': len(test_df)
        }
        
        with open('models/demand_production.pkl', 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info("💾 Modelo de demanda guardado en: models/demand_production.pkl")
        
        return model_data['metrics']
        
    except Exception as e:
        logger.error(f"❌ Error entrenando modelo de demanda: {e}")
        return None


# ===========================
# 3. ENTRENAR BERT (Sentiment Analysis)
# ===========================
def train_sentiment_model():
    """Entrenar modelo de sentimientos con datos reales"""
    try:
        from app.db.mongodb import mongodb_conn
        
        logger.info("=" * 60)
        logger.info("💬 ENTRENANDO MODELO DE ANÁLISIS DE SENTIMIENTOS")
        logger.info("=" * 60)
        
        db = mongodb_conn.connect()
        
        # Obtener comentarios
        logger.info("📊 Obteniendo comentarios desde MongoDB...")
        comments = list(db.user_feedback.find(
            {"comentario": {"$exists": True, "$ne": ""}},
            {"comentario": 1, "sentimiento": 1}
        ).limit(1000))
        
        logger.info(f"✅ {len(comments)} comentarios obtenidos")
        
        # Preparar datos
        texts = [c['comentario'] for c in comments]
        sentiments = [c.get('sentimiento', 'NEUTRAL') for c in comments]
        
        # Mapeo de sentimientos
        sentiment_map = {'POSITIVE': 1, 'NEUTRAL': 0, 'NEGATIVE': -1}
        y = [sentiment_map.get(s, 0) for s in sentiments]
        
        # Usar TF-IDF con clasificador simple
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.naive_bayes import MultinomialNB
        from sklearn.metrics import classification_report, accuracy_score, f1_score
        
        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            texts, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Vectorizar
        logger.info("🤖 Entrenando modelo TF-IDF + Naive Bayes...")
        vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            min_df=2
        )
        X_train_vec = vectorizer.fit_transform(X_train)
        X_test_vec = vectorizer.transform(X_test)
        
        # Entrenar
        model = MultinomialNB(alpha=0.1)
        model.fit(X_train_vec, y_train)
        
        # Predicciones
        y_pred = model.predict(X_test_vec)
        
        # Métricas
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        logger.info("📊 MÉTRICAS DEL MODELO:")
        logger.info(f"  Accuracy: {accuracy:.3f} ({accuracy*100:.1f}%)")
        logger.info(f"  F1-Score (weighted): {f1:.3f}")
        
        # Report detallado
        target_names = ['NEGATIVE', 'NEUTRAL', 'POSITIVE']
        report = classification_report(y_test, y_pred, target_names=target_names)
        logger.info("\n" + report)
        
        # Guardar modelo
        model_data = {
            'vectorizer': vectorizer,
            'model': model,
            'metrics': {
                'accuracy': float(accuracy),
                'f1_score': float(f1),
                'test_samples': len(y_test),
                'classes': target_names
            },
            'trained_at': datetime.now().isoformat()
        }
        
        with open('models/sentiment_production.pkl', 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info("💾 Modelo de sentimientos guardado en: models/sentiment_production.pkl")
        
        return model_data['metrics']
        
    except Exception as e:
        logger.error(f"❌ Error entrenando modelo de sentimientos: {e}")
        return None


# ===========================
# MAIN
# ===========================
def main():
    logger.info("\n" + "=" * 80)
    logger.info("🚀 ENTRENAMIENTO DE MODELOS DE PRODUCCIÓN")
    logger.info("=" * 80 + "\n")
    
    results = {}
    
    # 1. DBSCAN
    dbscan_metrics = train_dbscan_model()
    if dbscan_metrics:
        results['dbscan'] = dbscan_metrics
    
    print("\n")
    
    # 2. Demand Prediction
    demand_metrics = train_demand_model()
    if demand_metrics:
        results['demand'] = demand_metrics
    
    print("\n")
    
    # 3. Sentiment Analysis
    sentiment_metrics = train_sentiment_model()
    if sentiment_metrics:
        results['sentiment'] = sentiment_metrics
    
    # Guardar resumen
    logger.info("\n" + "=" * 80)
    logger.info("📊 RESUMEN DE MÉTRICAS DE TODOS LOS MODELOS")
    logger.info("=" * 80)
    
    with open('models/training_metrics.json', 'w') as f:
        import json
        json.dump(results, f, indent=2)
    
    logger.info("\n📋 DBSCAN:")
    if 'dbscan' in results:
        logger.info(f"  ✅ Silhouette Score: {results['dbscan']['silhouette_score']:.3f}")
        logger.info(f"  ✅ Davies-Bouldin Index: {results['dbscan']['davies_bouldin_index']:.3f}")
        logger.info(f"  ✅ Clusters: {results['dbscan']['n_clusters']}")
        logger.info(f"  ✅ Outliers: {results['dbscan']['n_outliers']} ({results['dbscan']['outlier_percentage']:.1f}%)")
    
    logger.info("\n📈 PREDICCIÓN DE DEMANDA:")
    if 'demand' in results:
        logger.info(f"  ✅ Precisión: {results['demand']['accuracy']:.1f}%")
        logger.info(f"  ✅ MAPE: {results['demand']['test_mape']:.2f}%")
        logger.info(f"  ✅ R²: {results['demand']['test_r2']:.3f}")
        logger.info(f"  ✅ MAE: {results['demand']['test_mae']:.2f} pasajeros")
    
    logger.info("\n💬 ANÁLISIS DE SENTIMIENTOS:")
    if 'sentiment' in results:
        logger.info(f"  ✅ Accuracy: {results['sentiment']['accuracy']*100:.1f}%")
        logger.info(f"  ✅ F1-Score: {results['sentiment']['f1_score']:.3f}")
    
    logger.info("\n💾 Métricas guardadas en: models/training_metrics.json")
    logger.info("\n" + "=" * 80)
    logger.info("✅ ENTRENAMIENTO COMPLETADO")
    logger.info("=" * 80 + "\n")


if __name__ == "__main__":
    main()
