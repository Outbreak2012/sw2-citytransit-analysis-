# 🚀 Guía Rápida para Iniciar el Sistema Completo

## Paso 1: Iniciar Docker Desktop

1. Abre Docker Desktop (ya lo hiciste ✅)
2. Haz clic en el botón **"Start"** para iniciar Docker Engine
3. Espera a que el ícono de Docker cambie a verde (20-30 segundos)

## Paso 2: Iniciar las Bases de Datos

Abre una terminal en la carpeta `analytics-service` y ejecuta:

```bash
cd "c:\Users\Camilo Sarmiento\Documents\2025\Software 2 Parcial 1\Nuevo\analytics-service"
docker-compose up -d
```

Esto iniciará:
- 🟢 **ClickHouse** (puerto 8123, 9000)
- 🟢 **MongoDB** (puerto 27017)
- 🟢 **Redis** (puerto 6379)

## Paso 3: Verificar que los Contenedores Estén Corriendo

```bash
docker ps
```

Deberías ver 3 contenedores:
- `citytransit-clickhouse`
- `citytransit-mongodb`
- `citytransit-redis`

## Paso 4: Iniciar el Servicio de Analytics (Backend)

En la misma terminal:

```bash
python start_simple.py
```

Verás:
```
============================================================
🚀 Iniciando CityTransit Analytics Service (Modo Simple)
============================================================
📚 Documentación API: http://localhost:8001/docs
💡 Health check: http://localhost:8001/health
============================================================
INFO:     Uvicorn running on http://0.0.0.0:8001
```

## Paso 5: Verificar el Frontend

El frontend ya está corriendo en: **http://localhost:3001**

Navega a: **http://localhost:3001/dashboard/ml**

El indicador debería cambiar de 🔴 **Servicio desconectado** a 🟢 **Analytics Service**

---

## 🔧 Comandos Útiles

### Detener todo:
```bash
# Detener Analytics Service: CTRL+C en su terminal

# Detener bases de datos:
docker-compose down

# Detener Docker Desktop: Clic en el menú de Docker Desktop
```

### Ver logs:
```bash
# Logs de Analytics:
# Ver en la terminal donde ejecutaste python start_simple.py

# Logs de contenedores:
docker logs citytransit-clickhouse
docker logs citytransit-mongodb
docker logs citytransit-redis
```

### Reiniciar bases de datos:
```bash
docker-compose restart
```

---

## ✅ Checklist de Verificación

- [ ] Docker Desktop iniciado (ícono verde)
- [ ] 3 contenedores corriendo (`docker ps`)
- [ ] Analytics Service en http://localhost:8001/health
- [ ] Frontend en http://localhost:3001
- [ ] Indicador 🟢 verde en /dashboard/ml

---

## 🐛 Solución de Problemas

### Docker no inicia:
- Reinicia Docker Desktop
- Verifica que WSL 2 esté instalado (si usas Windows)

### Puerto 8001 ocupado:
```bash
netstat -ano | findstr :8001
taskkill /F /PID [PID_NUMERO]
```

### Contenedores no inician:
```bash
docker-compose down
docker-compose up -d --force-recreate
```

### Analytics Service no conecta a las bases de datos:
Verifica el archivo `.env` en analytics-service:
```
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
MONGODB_URI=mongodb://admin:admin123@localhost:27017/citytransit?authSource=admin
REDIS_URL=redis://localhost:6379
```

---

**Una vez que todo esté verde, ¡tu sistema completo estará funcionando! 🎉**
