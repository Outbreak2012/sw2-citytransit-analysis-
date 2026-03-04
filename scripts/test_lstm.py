#!/usr/bin/env python3
"""Script para probar el modelo LSTM"""
import warnings
warnings.filterwarnings('ignore')
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml.lstm_model import lstm_predictor

print('=' * 60)
print('🧪 PRUEBA DEL MODELO LSTM - CityTransit')
print('=' * 60)

print('\n🔄 Cargando modelo LSTM...')
model = lstm_predictor.load_or_create_model()

if model is not None:
    print('✅ Modelo LSTM cargado exitosamente!')
    print(f'   Arquitectura: {model.count_params():,} parámetros')
    
    # Generar datos de prueba
    print('\n📊 Generando datos de prueba...')
    test_data = lstm_predictor.generate_synthetic_data(100)
    
    print('\n🔮 Generando predicciones con LSTM real...')
    predictions = lstm_predictor.predict(test_data, hours_ahead=24)
    
    print('\n📈 Predicciones para las próximas 24 horas:')
    print('-' * 50)
    for i, pred in enumerate(predictions):
        hour_label = f'Hora +{i+1:02d}'
        bar_len = min(int(pred / 5), 40)
        bar = '█' * bar_len
        print(f'   {hour_label}: {pred:6.1f} pasajeros {bar}')
    
    print('\n' + '=' * 60)
    print('✅ MODELO LSTM FUNCIONANDO CORRECTAMENTE')
    print('=' * 60)
else:
    print('❌ No se pudo cargar el modelo LSTM')
    print('   Ejecuta primero: python scripts/train_lstm.py')
