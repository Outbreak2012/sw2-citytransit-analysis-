#!/usr/bin/env python3
"""
Script para entrenar el modelo LSTM de predicción de demanda
============================================================
Este script genera datos sintéticos realistas y entrena el modelo LSTM.
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_realistic_demand_data(num_days: int = 90) -> pd.DataFrame:
    """
    Genera datos de demanda realistas para un sistema de transporte.
    Incluye patrones de hora pico, fines de semana y días festivos.
    """
    logger.info(f"📊 Generando {num_days} días de datos de demanda...")
    
    # Generar timestamps horarios
    start_date = datetime.now() - timedelta(days=num_days)
    dates = pd.date_range(start=start_date, periods=num_days * 24, freq='H')
    
    data = pd.DataFrame({'timestamp': dates})
    
    # Features temporales
    data['hour'] = data['timestamp'].dt.hour
    data['day_of_week'] = data['timestamp'].dt.dayofweek
    data['month'] = data['timestamp'].dt.month
    data['is_weekend'] = (data['day_of_week'] >= 5).astype(int)
    
    # Días festivos (aproximadamente 5% de los días)
    np.random.seed(42)
    holiday_days = np.random.choice(range(num_days), size=int(num_days * 0.05), replace=False)
    data['is_holiday'] = data['timestamp'].dt.date.apply(
        lambda x: 1 if (x - start_date.date()).days in holiday_days else 0
    )
    
    # Variables climáticas simuladas
    # Temperatura con variación estacional y diaria
    day_of_year = data['timestamp'].dt.dayofyear
    data['temperature'] = (
        20 + 
        10 * np.sin(2 * np.pi * day_of_year / 365) +  # Variación estacional
        5 * np.sin(2 * np.pi * data['hour'] / 24) +    # Variación diaria
        np.random.normal(0, 2, len(data))              # Ruido
    )
    
    # Precipitación (exponencial, mayormente 0)
    data['precipitation'] = np.random.exponential(1, len(data)) * np.random.choice([0, 1], len(data), p=[0.7, 0.3])
    
    # Eventos especiales (poisson)
    data['events_count'] = np.random.poisson(0.3, len(data))
    
    # ============================================
    # GENERAR DEMANDA REALISTA
    # ============================================
    
    base_demand = 100  # Demanda base
    
    # Efecto de hora del día (picos en mañana y tarde)
    hour_effect = np.zeros(len(data))
    for idx, hour in enumerate(data['hour']):
        if hour in [7, 8]:          # Pico mañana fuerte
            hour_effect[idx] = 80 + np.random.uniform(-10, 15)
        elif hour in [17, 18, 19]:  # Pico tarde fuerte
            hour_effect[idx] = 95 + np.random.uniform(-15, 20)
        elif hour in [9, 10, 11]:   # Mañana tardía
            hour_effect[idx] = 20 + np.random.uniform(-5, 10)
        elif hour in [12, 13]:      # Almuerzo
            hour_effect[idx] = 35 + np.random.uniform(-8, 12)
        elif hour in [14, 15, 16]:  # Tarde temprana
            hour_effect[idx] = 25 + np.random.uniform(-5, 10)
        elif hour in [20, 21, 22]:  # Noche temprana
            hour_effect[idx] = -20 + np.random.uniform(-10, 5)
        elif hour in [23, 0, 1, 2, 3, 4, 5]:  # Noche/madrugada
            hour_effect[idx] = -60 + np.random.uniform(-10, 5)
        else:  # 6am
            hour_effect[idx] = -30 + np.random.uniform(-5, 10)
    
    # Efecto de día de semana
    weekday_multiplier = data['day_of_week'].apply(
        lambda x: 1.0 if x < 5 else 0.6  # Fines de semana tienen 60% de demanda
    )
    
    # Efecto de festivos (reducción del 40%)
    holiday_multiplier = data['is_holiday'].apply(lambda x: 0.6 if x == 1 else 1.0)
    
    # Efecto de clima
    weather_effect = -data['precipitation'] * 5  # Lluvia reduce demanda
    temp_effect = -np.abs(data['temperature'] - 22) * 0.5  # Temperatura ideal ~22°C
    
    # Efecto de eventos
    events_effect = data['events_count'] * 15
    
    # Calcular demanda final
    data['demand'] = (
        (base_demand + hour_effect + weather_effect + temp_effect + events_effect) * 
        weekday_multiplier * 
        holiday_multiplier
    ).clip(10, 300)  # Limitar entre 10 y 300
    
    # Agregar features derivadas
    data['previous_demand'] = data['demand'].shift(1).fillna(data['demand'].mean())
    data['rolling_mean'] = data['demand'].rolling(window=6, min_periods=1).mean()
    
    logger.info(f"✅ Datos generados: {len(data)} registros")
    logger.info(f"📈 Demanda promedio: {data['demand'].mean():.2f}")
    logger.info(f"📈 Demanda mín/máx: {data['demand'].min():.2f} - {data['demand'].max():.2f}")
    
    return data


def train_lstm_model():
    """Entrena el modelo LSTM con datos sintéticos"""
    
    print("=" * 60)
    print("🚀 ENTRENAMIENTO DEL MODELO LSTM - CityTransit")
    print("=" * 60)
    
    # Importar después de configurar el path
    try:
        import tensorflow as tf
        print(f"✅ TensorFlow version: {tf.__version__}")
        print(f"✅ GPU disponible: {tf.config.list_physical_devices('GPU')}")
    except ImportError as e:
        print(f"❌ Error importando TensorFlow: {e}")
        return False
    
    from app.ml.lstm_model import lstm_predictor
    
    # 1. Generar datos de entrenamiento
    print("\n📊 Paso 1: Generando datos de entrenamiento...")
    train_data = generate_realistic_demand_data(num_days=90)
    
    # 2. Entrenar modelo
    print("\n🤖 Paso 2: Entrenando modelo LSTM...")
    print("   Esto puede tomar unos minutos...")
    
    try:
        history = lstm_predictor.train(
            data=train_data,
            epochs=30,
            batch_size=32
        )
        
        print("\n✅ Entrenamiento completado!")
        print(f"   - Loss final: {history['loss'][-1]:.4f}")
        print(f"   - Val Loss final: {history['val_loss'][-1]:.4f}")
        print(f"   - MAE final: {history['mae'][-1]:.4f}")
        
    except Exception as e:
        print(f"\n❌ Error durante entrenamiento: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. Probar predicciones
    print("\n🔮 Paso 3: Probando predicciones...")
    
    try:
        # Usar últimos datos para predecir
        test_data = train_data.tail(100)
        predictions = lstm_predictor.predict(test_data, hours_ahead=24)
        
        print(f"   Predicciones para las próximas 24 horas:")
        for i, pred in enumerate(predictions[:8]):
            print(f"   - Hora +{i+1}: {pred:.1f} pasajeros")
        print("   ...")
        
    except Exception as e:
        print(f"\n⚠️ Error en predicciones (pero el modelo está guardado): {e}")
    
    print("\n" + "=" * 60)
    print("✅ MODELO LSTM ENTRENADO Y GUARDADO EXITOSAMENTE")
    print("=" * 60)
    print(f"📁 Modelo guardado en: {lstm_predictor.model_path}")
    
    return True


if __name__ == "__main__":
    success = train_lstm_model()
    sys.exit(0 if success else 1)
