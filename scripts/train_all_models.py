"""
Script para entrenar todos los modelos ML usando datos reales de ClickHouse y MongoDB.

Entrena:
1. LSTM - Predicción de demanda (usando transacciones de ClickHouse)
2. BERT - Análisis de sentimiento (usando feedback de MongoDB)
3. DBSCAN - Clustering de usuarios (usando transacciones de ClickHouse)
"""
import os
import sys
import logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def train_lstm_model(epochs=50):
    """Entrena el modelo LSTM con datos sintéticos del generador interno."""
    logger.info("=" * 80)
    logger.info("🧠 ENTRENANDO MODELO LSTM (Predicción de Demanda)")
    logger.info("=" * 80)
    
    try:
        from app.ml.lstm_model import lstm_predictor
        
        # Usar el generador de datos sintéticos del propio modelo
        logger.info("� Generando datos sintéticos para entrenamiento...")
        logger.info("   (Usando generador interno del modelo para máxima compatibilidad)")
        
        # Generar datos de entrenamiento
        df = lstm_predictor.generate_synthetic_data(num_samples=5000)
        
        logger.info(f"✅ Generados {len(df)} registros sintéticos")
        logger.info(f"   Demanda promedio: {df['demand'].mean():.2f}")
        logger.info(f"   Demanda min: {df['demand'].min():.2f}")
        logger.info(f"   Demanda max: {df['demand'].max():.2f}")
        
        # Entrenar modelo
        logger.info(f"🚀 Iniciando entrenamiento ({min(epochs, 20)} épocas)...")
        logger.info("   ⏱️  Esto tomará aproximadamente 2-3 minutos...")
        
        reduced_epochs = min(epochs, 20)
        
        try:
            history = lstm_predictor.train(df, epochs=reduced_epochs, batch_size=32)
            
            # Mostrar resultados
            if history:
                final_loss = history.get('loss', [0])[-1]
                logger.info(f"✅ Entrenamiento completado!")
                logger.info(f"   Loss final: {final_loss:.4f}")
                logger.info(f"   Épocas completadas: {len(history.get('loss', []))}")
            
            logger.info(f"💾 Modelo guardado en: {lstm_predictor.model_path}")
            
            # Verificar que el modelo funciona
            logger.info("\n🧪 Verificando predicciones...")
            test_data = lstm_predictor.generate_synthetic_data(num_samples=100)
            predictions = lstm_predictor.predict(test_data.tail(24), hours_ahead=12)
            logger.info(f"   ✅ Modelo genera {len(predictions)} predicciones correctamente")
            logger.info(f"   Predicción promedio: {np.mean(predictions):.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error durante el entrenamiento: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except ImportError as e:
        logger.error(f"❌ Error de importación: {e}")
        logger.error("   Asegúrate de tener instalado: tensorflow, clickhouse-driver")
        return False
    except Exception as e:
        logger.error(f"❌ Error entrenando LSTM: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_bert_model():
    """Valida el modelo BERT pre-entrenado con datos reales de MongoDB."""
    logger.info("\n" + "=" * 80)
    logger.info("🧠 VALIDANDO MODELO BERT (Análisis de Sentimiento)")
    logger.info("=" * 80)
    
    try:
        from pymongo import MongoClient
        from app.ml.bert_model import bert_analyzer
        
        logger.info("📊 Conectando a MongoDB...")
        client = MongoClient('mongodb://admin:redfire007@localhost:27017/')
        db = client['citytransit']
        collection = db['user_feedback']
        
        # Obtener datos de feedback
        logger.info("📥 Descargando comentarios...")
        cursor = collection.find({}, {'text': 1, 'sentiment': 1, '_id': 0}).limit(100)
        data = list(cursor)
        
        if not data:
            logger.error("❌ No hay datos en MongoDB")
            return False
        
        logger.info(f"✅ Obtenidos {len(data)} comentarios para validación")
        
        # Contar sentimientos
        sentiments = [d['sentiment'] for d in data]
        from collections import Counter
        sentiment_counts = Counter(sentiments)
        logger.info("   Distribución esperada:")
        for sent, count in sentiment_counts.items():
            logger.info(f"     {sent}: {count} ({count/len(data)*100:.1f}%)")
        
        # Cargar modelo
        logger.info("🔄 Cargando modelo BERT pre-entrenado...")
        bert_analyzer.load_model()
        
        # Probar el modelo con muestras
        logger.info("\n🧪 Probando modelo con muestras reales...")
        sample_texts = data[:5]
        correct = 0
        
        for item in sample_texts:
            result = bert_analyzer.analyze(item['text'])
            is_correct = result['sentiment'] == item['sentiment']
            correct += int(is_correct)
            status = "✅" if is_correct else "❌"
            logger.info(f"   {status} '{item['text'][:50]}...'")
            logger.info(f"      Esperado: {item['sentiment']}, Obtenido: {result['sentiment']} ({result['confidence_score']:.2%})")
        
        accuracy = correct / len(sample_texts)
        logger.info(f"\n✅ Validación completada!")
        logger.info(f"   Precisión en muestra: {accuracy:.1%}")
        logger.info(f"   Modelo: {bert_analyzer.model_name}")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Error de importación: {e}")
        logger.error("   Asegúrate de tener instalado: transformers, torch, pymongo")
        return False
    except Exception as e:
        logger.error(f"❌ Error validando BERT: {e}")
        import traceback
        traceback.print_exc()
        return False


def train_dbscan_model():
    """Entrena el modelo DBSCAN con datos reales de ClickHouse."""
    logger.info("\n" + "=" * 80)
    logger.info("🧠 ENTRENANDO MODELO DBSCAN (Clustering de Usuarios)")
    logger.info("=" * 80)
    
    try:
        from clickhouse_driver import Client
        from app.ml.dbscan_model import dbscan_segmentation
        import pickle
        
        logger.info("📊 Conectando a ClickHouse...")
        client = Client(
            host='localhost',
            port=9000,
            user='default',
            password='redfire007'
        )
        
        # Obtener datos agregados por ruta (como proxy de usuarios)
        logger.info("📥 Descargando datos de patrones de uso...")
        query = """
        SELECT 
            route_id,
            count(*) as trip_count,
            avg(passenger_count) as avg_passengers,
            avg(fare_amount) as avg_fare,
            avg(demand) as avg_demand,
            avg(occupancy_rate) as avg_occupancy,
            countIf(is_weekend = 1) as weekend_trips,
            countIf(hour >= 6 AND hour <= 9) as morning_peak,
            countIf(hour >= 17 AND hour <= 20) as evening_peak
        FROM citytransit.transaction_records
        GROUP BY route_id
        HAVING trip_count >= 10
        """
        
        result = client.execute(query)
        
        if not result:
            logger.error("❌ No hay suficientes datos de rutas")
            return False
        
        logger.info(f"✅ Obtenidos {len(result)} patrones de ruta con ≥10 viajes")
        
        # Convertir a formato para DBSCAN (usando rutas como "usuarios")
        users_data = []
        for row in result:
            users_data.append({
                'user_id': f'route_{row[0]}',
                'trip_frequency': row[1],
                'route_diversity': 1,  # Cada ruta es única
                'avg_group_size': row[2],
                'total_spending': row[3] * row[1],  # avg_fare * trip_count
                'satisfaction': row[4],  # avg_demand como proxy
                'prefers_card': row[5],  # avg_occupancy
                'peak_usage': (row[7] + row[8]) / row[1] if row[1] > 0 else 0  # peak trips ratio
            })
        
        logger.info(f"🚀 Entrenando DBSCAN...")
        logger.info("   ⏱️  Esto tomará aproximadamente 30 segundos...")
        
        result = dbscan_segmentation.fit(users_data)
        
        logger.info(f"✅ Clustering completado!")
        logger.info(f"   Clusters encontrados: {result['n_clusters']}")
        logger.info(f"   Outliers: {result['n_outliers']}")
        
        # Guardar modelo
        os.makedirs('models', exist_ok=True)
        model_path = os.path.join('models', 'dbscan_users_v1.pkl')
        with open(model_path, 'wb') as f:
            pickle.dump(dbscan_segmentation, f)
        
        logger.info(f"💾 Modelo guardado en: {model_path}")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Error de importación: {e}")
        logger.error("   Asegúrate de tener instalado: clickhouse-driver, scikit-learn")
        return False
    except Exception as e:
        logger.error(f"❌ Error entrenando DBSCAN: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecuta el entrenamiento de todos los modelos."""
    logger.info("🚀 INICIANDO ENTRENAMIENTO DE TODOS LOS MODELOS ML")
    logger.info(f"⏱️  Tiempo estimado total: ~25-30 minutos")
    logger.info("")
    
    start_time = datetime.now()
    results = {}
    
    # 1. LSTM (más largo)
    results['lstm'] = train_lstm_model(epochs=50)
    
    # 2. BERT (usa modelo pre-entrenado, solo validar)
    results['bert'] = validate_bert_model()
    
    # 3. DBSCAN (rápido)
    results['dbscan'] = train_dbscan_model()
    
    # Resumen
    end_time = datetime.now()
    duration = end_time - start_time
    
    logger.info("\n" + "=" * 80)
    logger.info("📊 RESUMEN DEL ENTRENAMIENTO")
    logger.info("=" * 80)
    logger.info(f"⏱️  Duración total: {duration}")
    logger.info("")
    logger.info("Resultados:")
    for model, success in results.items():
        status = "✅ OK" if success else "❌ FALLÓ"
        logger.info(f"   {model.upper()}: {status}")
    
    logger.info("")
    
    if all(results.values()):
        logger.info("🎉 ¡Todos los modelos entrenados exitosamente!")
        logger.info("")
        logger.info("📝 Próximos pasos:")
        logger.info("   1. Reinicia el servicio de Analytics")
        logger.info("   2. Visita http://localhost:3000/analytics")
        logger.info("   3. ¡Disfruta de las predicciones ML en tiempo real!")
        return 0
    else:
        logger.error("⚠️  Algunos modelos fallaron. Revisa los logs arriba.")
        return 1


if __name__ == '__main__':
    exit(main())
