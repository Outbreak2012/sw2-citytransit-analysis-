# 🚀 Guía de Inicio Rápido - CityTransit

## 📋 Requisitos Previos

### ✅ Software Necesario

1. **Docker Desktop** (Recomendado)
   - Descarga: https://www.docker.com/products/docker-desktop
   - Versión: 20.10 o superior

2. **Java 17+**
   - Actualmente configurado: Java 21
   - Ubicación: `C:\Users\Camilo Sarmiento\AppData\Roaming\Code\User\globalStorage\pleiades.java-extension-pack-jdk\java\21`

3. **Node.js 18+**
   - Descarga: https://nodejs.org/
   - Incluye npm

4. **Python 3.11+**
   - Descarga: https://www.python.org/downloads/
   - Asegúrate de agregar al PATH

---

## 🎯 Inicio Rápido (3 Pasos)

### Opción A: Todo Automático con Scripts

```bash
# 1. Levantar bases de datos
.\INICIAR-TODO.bat

# Espera a que aparezca: "✅ Sistema CityTransit iniciado completamente"
```

### Opción B: Manual Paso a Paso

#### **Paso 1: Bases de Datos (Docker)**
```bash
cd citytransit-backend
docker-compose -f docker-compose-database.yml up -d
```

Espera 30 segundos para que las bases de datos inicien.

**Verificar:**
```bash
docker ps
```

Deberías ver:
- ✅ citytransit-postgres (puerto 5432)
- ✅ citytransit-mongodb (puerto 27017)
- ✅ citytransit-redis (puerto 6379)
- ✅ citytransit-pgadmin (puerto 5050)

---

#### **Paso 2: Backend (Spring Boot)**

```bash
# Compilar (solo primera vez o después de cambios)
cd citytransit-backend
mvnw.cmd clean package -DskipTests

# Iniciar backend
.\start-backend.bat
```

**O iniciar con Maven directamente:**
```bash
mvnw.cmd spring-boot:run
```

**Verificar:**
- Backend: http://localhost:8080
- GraphiQL: http://localhost:8080/graphiql
- Swagger: http://localhost:8080/swagger-ui.html
- Health: http://localhost:8080/actuator/health

---

#### **Paso 3: Frontend (Next.js)**

```bash
# Instalar dependencias (solo primera vez)
cd citytransit-web
npm install

# Iniciar frontend
npm run dev
```

**Verificar:**
- Frontend: http://localhost:3000

---

#### **Paso 4 (Opcional): Analytics Service (Python)**

```bash
cd analytics-service

# Crear entorno virtual (solo primera vez)
python -m venv venv

# Activar entorno
venv\Scripts\activate

# Instalar dependencias (solo primera vez)
pip install -r requirements.txt

# Iniciar servicio
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**O usar Docker:**
```bash
cd analytics-service
docker-compose up -d
```

**Verificar:**
- Analytics API: http://localhost:8000
- Docs: http://localhost:8000/docs

---

## 🔑 Credenciales de Acceso

### Frontend Login
```
Email: admin@citytransit.com
Password: admin123
```

### PgAdmin (PostgreSQL UI)
```
URL: http://localhost:5050
Email: admin@citytransit.com
Password: admin123
```

**Conectar a PostgreSQL desde PgAdmin:**
- Host: postgres (o localhost)
- Port: 5432
- Database: citytransit_db
- Username: citytransit_user
- Password: citytransit_password123

### MongoDB
```
URL: mongodb://admin:admin123@localhost:27017/citytransit_analytics
```

### ClickHouse (Analytics)
```
URL: http://localhost:8123
User: admin
Password: admin123
Database: citytransit
```

---

## 🛑 Detener Servicios

### Detener Bases de Datos
```bash
cd citytransit-backend
docker-compose -f docker-compose-database.yml down
```

### Detener Analytics
```bash
cd analytics-service
docker-compose down
```

### Detener Backend
- Presiona `Ctrl+C` en la terminal del backend

### Detener Frontend
- Presiona `Ctrl+C` en la terminal del frontend

---

## 🔧 Solución de Problemas

### Error: "Puerto ya en uso"

**Backend (8080):**
```bash
# Windows
netstat -ano | findstr :8080
taskkill /PID [número_pid] /F
```

**Frontend (3000):**
```bash
netstat -ano | findstr :3000
taskkill /PID [número_pid] /F
```

### Error: "Docker containers no inician"

```bash
# Limpiar y reiniciar
docker-compose -f docker-compose-database.yml down -v
docker-compose -f docker-compose-database.yml up -d
```

### Error: "Java no encontrado"

Verifica que JAVA_HOME esté configurado:
```bash
echo %JAVA_HOME%
java -version
```

### Error: "mvnw.cmd no funciona"

Usa Maven global:
```bash
mvn clean package -DskipTests
mvn spring-boot:run
```

### Error: "npm install falla"

```bash
# Limpiar cache
npm cache clean --force
rm -rf node_modules
rm package-lock.json
npm install
```

### Error: "Python no encontrado"

Asegúrate de que Python esté en el PATH:
```bash
python --version
pip --version
```

---

## 📊 Verificación de Servicios

### Script de Verificación
```bash
# Backend
curl http://localhost:8080/actuator/health

# Frontend
curl http://localhost:3000

# Analytics
curl http://localhost:8000/health

# PostgreSQL
docker exec citytransit-postgres pg_isready -U citytransit_user

# MongoDB
docker exec citytransit-mongodb mongosh --eval "db.adminCommand('ping')"

# Redis
docker exec citytransit-redis redis-cli ping
```

---

## 🎨 URLs de Acceso Rápido

| Servicio | URL | Puerto |
|----------|-----|--------|
| Frontend | http://localhost:3000 | 3000 |
| Backend API | http://localhost:8080 | 8080 |
| GraphiQL | http://localhost:8080/graphiql | 8080 |
| Swagger UI | http://localhost:8080/swagger-ui.html | 8080 |
| Analytics API | http://localhost:8000 | 8000 |
| Analytics Docs | http://localhost:8000/docs | 8000 |
| PgAdmin | http://localhost:5050 | 5050 |
| PostgreSQL | localhost | 5432 |
| MongoDB | localhost | 27017 |
| Redis | localhost | 6379 |
| ClickHouse | localhost | 8123, 9000 |

---

## 🔄 Orden de Inicio Recomendado

1. **Bases de datos (Docker)** → Esperar 30 segundos
2. **Backend (Spring Boot)** → Esperar que termine de cargar
3. **Frontend (Next.js)** → Listo en ~10 segundos
4. **Analytics (Opcional)** → Listo en ~5 segundos

---

## 📝 Notas Importantes

- **Primera ejecución**: Tarda más porque descarga dependencias
- **Compilación Backend**: `mvnw clean package` puede tardar 2-3 minutos
- **Npm install**: Primera vez tarda ~1-2 minutos
- **Docker pull**: Primera vez descarga imágenes (~500MB)

---

## 🆘 Ayuda Adicional

- Backend README: `citytransit-backend/README.md`
- Frontend README: `citytransit-web/README.md`
- Analytics README: `analytics-service/README.md`
- GraphQL Guide: `citytransit-web/GRAPHQL_GUIDE.md`
- Database Setup: `citytransit-backend/DATABASE_SETUP.md`

---

## ✅ Checklist de Inicio

- [ ] Docker Desktop instalado y ejecutándose
- [ ] Java 17+ instalado (`java -version`)
- [ ] Node.js 18+ instalado (`node -v`)
- [ ] Python 3.11+ instalado (opcional) (`python --version`)
- [ ] Puertos 3000, 8080, 5432, 27017, 6379 disponibles
- [ ] Bases de datos levantadas (`docker ps`)
- [ ] Backend iniciado (http://localhost:8080/actuator/health)
- [ ] Frontend iniciado (http://localhost:3000)
- [ ] Login exitoso en el frontend

---

¡Tu sistema CityTransit está listo para usar! 🎉
