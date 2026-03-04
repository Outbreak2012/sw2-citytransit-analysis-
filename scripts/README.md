# 🤖 Scripts de Entrenamiento ML - CityTransit Analytics

## 📋 Descripción

Scripts para poblar bases de datos con datos sintéticos realistas y entrenar modelos de Machine Learning.

## 🎯 Scripts Disponibles

### 1. `populate_clickhouse.py`
Genera y pobla ClickHouse con transacciones históricas sintéticas (6 meses).

**Datos generados:**
- ✅ 43,200+ transacciones (10 rutas × 24 horas × 180 días)
- ✅ Patrones horarios realistas (horas pico: 6-8am, 5-7pm)
- ✅ Variación por día de semana y festivos
- ✅ Datos de clima (temperatura, precipitación)
- ✅ Eventos especiales
- ✅ Tasas de ocupación

**Uso:**
```bash
cd analytics-service
python scripts/populate_clickhouse.py
```

**Tiempo estimado:** 2-3 minutos

---

### 2. `populate_mongodb.py`
Genera y pobla MongoDB con feedback de usuarios (comentarios, ratings).

**Datos generados:**
- ✅ 5,000 comentarios en español
- ✅ Distribución: 40% positivos, 35% neutrales, 25% negativos
- ✅ Ratings de 1-5 estrellas
- ✅ Categorización (puntualidad, limpieza, conductor, etc.)
- ✅ Metadata de modelos ML

**Uso:**
```bash
cd analytics-service
python scripts/populate_mongodb.py
```

**Tiempo estimado:** 30 segundos

---

### 3. `run_complete_pipeline.py`
**Pipeline completo:** Pobla datos + Entrena todos los modelos

**Uso:**
```bash
cd analytics-service

# Pipeline completo (datos + entrenamiento)
python scripts/run_complete_pipeline.py

# Solo entrenar (datos ya existen)
python scripts/run_complete_pipeline.py --skip-data

# Personalizar epochs
python scripts/run_complete_pipeline.py --lstm-epochs 100 --bert-epochs 10
```

**Tiempo estimado:** 20-30 minutos (con TensorFlow instalado)

---

## 🚀 Guía Rápida de Uso

### Opción A: Todo Automático (Recomendado)

```bash
# 1. Instalar dependencias ML (opcional pero recomendado)
pip install tensorflow==2.18.0
pip install transformers torch

# 2. Ejecutar pipeline completo
cd analytics-service
python scripts/run_complete_pipeline.py

# 3. Reiniciar servicio
python start_simple.py
```

### Opción B: Paso a Paso

```bash
# 1. Poblar ClickHouse
python scripts/populate_clickhouse.py

# 2. Poblar MongoDB
python scripts/populate_mongodb.py

# 3. Entrenar modelos (si tienes TensorFlow/Transformers)
python scripts/train_models.py --model all

# 4. O usar fallbacks (sin entrenar)
python start_simple.py
```

---

## 📊 Datos Sintéticos Generados

### ClickHouse - transaction_records

```sql
SELECT COUNT(*) FROM citytransit.transaction_records;
-- ~43,200 registros

SELECT route_id, AVG(demand) as avg_demand, AVG(occupancy_rate) as avg_occupancy
FROM citytransit.transaction_records
GROUP BY route_id;
```

**Características de los datos:**
- **Patrones horarios realistas:**
  - 6-8am: Alta demanda (horas pico mañana)
  - 9am-4pm: Demanda media (horario laboral)
  - 5-7pm: Alta demanda (horas pico tarde)
  - 8pm-5am: Baja demanda (noche/madrugada)

- **Factores climáticos:**
  - Temperatura promedio: 18-20°C (Bogotá)
  - Precipitación: Mayor en abril-mayo, octubre-noviembre
  - Efecto lluvia: Reduce demanda ~10-15%

- **Factores especiales:**
  - Festivos: Reduce demanda laboral ~40%
  - Fin de semana: Reduce demanda ~30%
  - Eventos: Aumenta demanda ~15% por evento

### MongoDB - user_feedback

```javascript
db.user_feedback.countDocuments()
// 5,000 documentos

db.user_feedback.aggregate([
  { $group: { _id: "$sentiment", count: { $sum: 1 } } }
])
// POSITIVE: ~2,000 (40%)
// NEUTRAL: ~1,750 (35%)
// NEGATIVE: ~1,250 (25%)
```

**Ejemplo de comentario:**
```json
{
  "user_id": 42,
  "route_id": 3,
  "text": "Excelente servicio, muy puntual y limpio. Lo recomiendo!",
  "rating": 5,
  "sentiment": "POSITIVE",
  "confidence": 0.92,
  "timestamp": "2024-08-15T14:30:00Z",
  "source": "mobile_app",
  "category": "puntualidad"
}
```

---

## 🤖 Modelos a Entrenar

### 1. LSTM - Predicción de Demanda

**Input:** 
- Datos históricos de 6 meses
- Features: hour, day_of_week, is_weekend, temperature, events, etc.

**Output:**
- Predicciones de demanda para próximas 24-48 horas
- Modelo guardado en: `models/lstm_demand_v1.h5`

**Métricas esperadas:**
- MAE < 10 pasajeros
- MAPE < 15%
- R² > 0.80

**Tiempo de entrenamiento:** ~10-15 minutos (50 epochs)

---

### 2. BERT - Análisis de Sentimientos

**Input:**
- 5,000 comentarios etiquetados (español)
- Distribución: 40% pos, 35% neu, 25% neg

**Output:**
- Modelo fine-tuned para clasificación de sentimientos
- Modelo guardado en: `models/bert_sentiment_v1/`

**Métricas esperadas:**
- Accuracy > 85%
- F1-Score > 0.82

**Tiempo de entrenamiento:** ~5-10 minutos (5 epochs)

---

### 3. DBSCAN - Segmentación de Usuarios

**Input:**
- Patrones de uso de 1,000 usuarios
- Features: frecuencia, rutas, horarios, gasto

**Output:**
- 4-6 clusters identificados
- Modelo guardado en: `models/dbscan_users_v1.pkl`

**Métricas esperadas:**
- Silhouette Score > 0.5
- % Outliers < 10%

**Tiempo de entrenamiento:** ~30 segundos

---

## 🛠️ Troubleshooting

### Error: "ClickHouse connection failed"
```bash
# Verificar que ClickHouse esté corriendo
docker ps | grep clickhouse

# Si no está, iniciar
docker-compose up -d clickhouse
```

### Error: "MongoDB connection refused"
```bash
# Verificar que MongoDB esté corriendo
docker ps | grep mongo

# Si no está, iniciar
docker-compose up -d mongodb
```

### Error: "TensorFlow not found"
```bash
# Instalar TensorFlow
pip install tensorflow==2.18.0

# O usar fallbacks sin TensorFlow
python start_simple.py  # Funciona sin TF
```

### Error: "Transformers not found"
```bash
# Instalar Transformers y PyTorch
pip install transformers torch

# O usar fallbacks sin Transformers
python start_simple.py  # Funciona sin Transformers
```

---

## 📈 Verificar Datos Generados

### ClickHouse

```bash
# Conectar a ClickHouse
clickhouse-client

# Ver estadísticas
SELECT 
    COUNT(*) as total,
    MIN(timestamp) as fecha_inicio,
    MAX(timestamp) as fecha_fin,
    AVG(demand) as demanda_promedio,
    AVG(occupancy_rate) as ocupacion_promedio
FROM citytransit.transaction_records;

# Ver demanda por ruta
SELECT 
    route_id,
    AVG(demand) as demanda_promedio,
    COUNT(*) as num_registros
FROM citytransit.transaction_records
GROUP BY route_id
ORDER BY demanda_promedio DESC;
```

### MongoDB

```bash
# Conectar a MongoDB
mongosh citytransit

# Ver estadísticas de feedback
db.user_feedback.aggregate([
  {
    $group: {
      _id: "$sentiment",
      count: { $sum: 1 },
      avg_rating: { $avg: "$rating" },
      avg_confidence: { $avg: "$confidence" }
    }
  }
])

# Ver comentarios recientes
db.user_feedback.find().sort({timestamp: -1}).limit(10).pretty()
```

---

## 🎯 Próximos Pasos

Después de ejecutar los scripts:

1. ✅ **Verificar datos** con las queries de arriba
2. ✅ **Entrenar modelos** (si tienes TensorFlow/Transformers)
3. ✅ **Reiniciar servicio** para cargar modelos
4. ✅ **Probar endpoints** en http://localhost:8001/docs
5. ✅ **Integrar con frontend** (dashboard)

---

## 📝 Notas

- Los datos sintéticos son **realistas** y basados en patrones del mundo real
- Los modelos pueden entrenarse con datos reales cuando estén disponibles
- El servicio funciona **sin entrenar** usando fallbacks inteligentes
- Los fallbacks generan predicciones razonables para demos/desarrollo

---

## 🎉 ¿Listo para producción?

Una vez entrenados los modelos con datos reales:

1. Los modelos se cargan automáticamente al iniciar el servicio
2. El sistema detecta si hay modelos entrenados disponibles
3. Si no hay modelos, usa fallbacks automáticamente
4. No hay cambios de código necesarios - todo es plug-and-play
