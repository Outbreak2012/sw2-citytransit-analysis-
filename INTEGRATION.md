# CityTransit Analytics Service - Integration Guide

## 🔗 Integración con Backend Java

### Arquitectura

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────┐
│                 │         │                  │         │             │
│  Frontend       │────────▶│  Backend Java    │────────▶│  PostgreSQL │
│  (React/Vue)    │         │  (Spring Boot)   │         │             │
│                 │         │                  │         └─────────────┘
└─────────────────┘         └──────────────────┘
        │                           │
        │                           │
        │                    ┌──────▼──────────┐
        │                    │                 │
        └───────────────────▶│  Analytics      │
                             │  Service        │
                             │  (FastAPI)      │
                             │                 │
                             └─────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
             ┌──────▼──────┐  ┌─────▼─────┐  ┌──────▼─────┐
             │             │  │           │  │            │
             │ ClickHouse  │  │  MongoDB  │  │   Redis    │
             │             │  │           │  │            │
             └─────────────┘  └───────────┘  └────────────┘
```

## 🚀 Endpoints Principales

### 1. Predicción de Demanda (LSTM)
```bash
# Predecir demanda para una ruta
curl -X POST http://localhost:8001/api/v1/analytics/demand/predict \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "route_id": 1,
    "hours_ahead": 24,
    "include_weather": true,
    "include_events": true
  }'
```

### 2. Segmentación de Usuarios (DBSCAN)
```bash
# Segmentar usuarios
curl -X POST http://localhost:8001/api/v1/analytics/users/segment \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "eps": 0.5,
    "min_samples": 5
  }'
```

### 3. Análisis de Sentimientos (BERT)
```bash
# Analizar sentimiento
curl -X POST http://localhost:8001/api/v1/analytics/sentiment/analyze \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Excelente servicio, muy puntual",
    "source": "feedback",
    "user_id": 29
  }'
```

### 4. Dashboard y KPIs
```bash
# Obtener KPIs
curl -X GET http://localhost:8001/api/v1/reports/kpis \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Dashboard completo
curl -X GET http://localhost:8001/api/v1/reports/dashboard?period=daily \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 📊 Casos de Uso

### 1. Optimización de Rutas
```python
# El servicio analítico predice demanda futura
# Backend ajusta frecuencia de buses basándose en predicciones
```

### 2. Marketing Personalizado
```python
# DBSCAN identifica clusters de usuarios
# Backend envía notificaciones personalizadas por cluster
```

### 3. Mejora de Servicio
```python
# BERT analiza feedback de usuarios
# Backend genera alertas automáticas para issues negativos
```

## 🔐 Autenticación

El servicio comparte el mismo sistema JWT del backend:

```python
# Token JWT del backend es válido para Analytics Service
headers = {
    "Authorization": f"Bearer {access_token}"
}
```

## 📝 Logs del Sistema

```bash
# Ver logs del Analytics Service
docker logs -f paytransit-analytics

# Ver logs del Backend
docker logs -f paytransit-backend
```

## 🧪 Testing

```bash
# Test de health check
curl http://localhost:8001/health

# Test de autenticación
# 1. Login en backend
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@citytransit.com","password":"Admin123!"}'

# 2. Usar token en Analytics
curl -X GET http://localhost:8001/api/v1/reports/kpis \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 📈 Métricas y Monitoreo

- **Backend**: http://localhost:8080/actuator/metrics
- **Analytics**: http://localhost:8001/api/v1/reports/performance

## 🔄 Flujo de Datos

1. **Usuario realiza transacción** → Backend guarda en PostgreSQL
2. **Backend envía eventos** → ClickHouse (análisis) y MongoDB (reportes)
3. **Analytics Service procesa** → Genera predicciones y análisis
4. **Dashboard consulta** → Analytics Service retorna insights
5. **Backend actúa** → Toma decisiones basadas en análisis

## 🎯 Próximos Pasos

1. ✅ Servicios levantados
2. ✅ Usuario admin creado
3. ✅ Analytics Service integrado
4. 🔄 Testing de endpoints
5. 🔄 Integración con frontend
6. 🔄 Configuración de alertas automáticas
