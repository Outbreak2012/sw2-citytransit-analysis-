#!/bin/bash
# ========================================
#   CityTransit - Detener Todo el Sistema
# ========================================

echo ""
echo "========================================"
echo "   CityTransit - Deteniendo Sistema"
echo "========================================"
echo ""

# Detener bases de datos
echo "[1/3] Deteniendo bases de datos Docker..."
cd citytransit-backend
docker-compose -f docker-compose-database.yml down
echo "✅ OK - Bases de datos detenidas"
echo ""

# Detener analytics (si existe)
echo "[2/3] Deteniendo Analytics Service..."
cd ../analytics-service
if [ -f "docker-compose.yml" ]; then
    docker-compose down
    echo "✅ OK - Analytics detenido"
else
    echo "⚠️  Analytics no configurado con Docker"
fi
echo ""

# Detener procesos
echo "[3/3] Deteniendo procesos Backend y Frontend..."

# Leer y matar PIDs guardados
cd ..
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    kill $BACKEND_PID 2>/dev/null
    rm .backend.pid
    echo "✅ Backend detenido (PID: $BACKEND_PID)"
fi

if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    kill $FRONTEND_PID 2>/dev/null
    rm .frontend.pid
    echo "✅ Frontend detenido (PID: $FRONTEND_PID)"
fi

# Detener por puertos como respaldo
lsof -ti:8080 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null
lsof -ti:8000 | xargs kill -9 2>/dev/null

echo ""
echo "========================================"
echo "   ✅ SISTEMA DETENIDO COMPLETAMENTE"
echo "========================================"
echo ""
echo "Contenedores Docker restantes:"
docker ps
echo ""
