#!/bin/bash
# ========================================
#   CityTransit - Iniciar Todo el Sistema
# ========================================

echo ""
echo "========================================"
echo "   CityTransit - Sistema Completo"
echo "========================================"
echo ""
echo "Este script iniciará:"
echo "  1. Bases de datos (PostgreSQL, MongoDB, Redis)"
echo "  2. Backend (Spring Boot en puerto 8080)"
echo "  3. Frontend (Next.js en puerto 3000)"
echo ""

# Verificar Docker
echo "[1/6] Verificando Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ ERROR: Docker no está instalado"
    echo "Por favor instala Docker desde: https://www.docker.com/products/docker-desktop"
    exit 1
fi
echo "✅ OK - Docker detectado"
echo ""

# Verificar Java
echo "[2/6] Verificando Java..."
if ! command -v java &> /dev/null; then
    echo "❌ ERROR: Java no está instalado"
    echo "Por favor instala Java 17+ desde: https://adoptium.net/"
    exit 1
fi
echo "✅ OK - Java detectado"
echo ""

# Verificar Node.js
echo "[3/6] Verificando Node.js..."
if ! command -v node &> /dev/null; then
    echo "❌ ERROR: Node.js no está instalado"
    echo "Por favor instala Node.js desde: https://nodejs.org/"
    exit 1
fi
echo "✅ OK - Node.js detectado"
echo ""

# Iniciar bases de datos
echo "[4/6] Iniciando bases de datos con Docker..."
cd citytransit-backend
docker-compose -f docker-compose-database.yml up -d
if [ $? -ne 0 ]; then
    echo "❌ ERROR: No se pudieron iniciar las bases de datos"
    exit 1
fi
echo "✅ OK - Bases de datos iniciadas"
echo ""
echo "⏳ Esperando 30 segundos para que las bases de datos estén listas..."
sleep 30
echo ""

# Verificar si el JAR existe
echo "[5/6] Verificando backend..."
if [ ! -f "target/citytransit-backend-1.0.0.jar" ]; then
    echo "📦 El archivo JAR no existe. Compilando proyecto..."
    ./mvnw clean package -DskipTests
    if [ $? -ne 0 ]; then
        echo "❌ ERROR: No se pudo compilar el backend"
        exit 1
    fi
fi
echo "✅ OK - Backend compilado"
echo ""

# Verificar node_modules
echo "[6/6] Verificando frontend..."
cd ../citytransit-web
if [ ! -d "node_modules" ]; then
    echo "📦 Instalando dependencias del frontend..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ ERROR: No se pudieron instalar las dependencias del frontend"
        exit 1
    fi
fi
echo "✅ OK - Frontend listo"
echo ""

echo "========================================"
echo "   INICIANDO SERVICIOS"
echo "========================================"
echo ""

# Iniciar backend en segundo plano
cd ../citytransit-backend
echo "🚀 Iniciando Backend en puerto 8080..."
./mvnw spring-boot:run &
BACKEND_PID=$!

# Esperar 15 segundos
echo "⏳ Esperando 15 segundos para que el backend inicie..."
sleep 15

# Iniciar frontend en segundo plano
cd ../citytransit-web
echo "🚀 Iniciando Frontend en puerto 3000..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "   ✅ SISTEMA INICIADO"
echo "========================================"
echo ""
echo "📍 URLs de acceso:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8080"
echo "   GraphiQL:  http://localhost:8080/graphiql"
echo "   Swagger:   http://localhost:8080/swagger-ui.html"
echo "   PgAdmin:   http://localhost:5050"
echo ""
echo "🔑 Credenciales:"
echo "   Email:     admin@citytransit.com"
echo "   Password:  admin123"
echo ""
echo "⚠️  Para detener el sistema, presiona Ctrl+C"
echo "    O ejecuta: ./DETENER-TODO.sh"
echo ""

# Guardar PIDs
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

# Esperar
wait
